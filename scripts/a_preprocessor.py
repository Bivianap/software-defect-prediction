from turtle import mode
import pandas as pd
import unidecode
import re
import os
import hashlib
from rapidfuzz import process, fuzz
from sklearn.preprocessing import OneHotEncoder
import joblib
from config import STRING_COLUMNS, COLUMNS_TO_DROP, BUG_ID_FIELD, THRESHOLD_CONTRIB_HIGH, THRESHOLD_CONTRIB_LOW


# This file makes validation of bugs in the commits
###############################################################

# Define what text columns you want to scale by categories
selected_text_cols = STRING_COLUMNS


# path
data_folder = os.path.join("..", "data", "info")
if not os.path.exists(data_folder):
    os.makedirs(data_folder)

data_folder_preprocess = os.path.join("..", "data", "preprocess")
if not os.path.exists(data_folder_preprocess):
    os.makedirs(data_folder_preprocess)

data_folder_models = os.path.join("..", "models")
if not os.path.exists(data_folder_models):
    os.makedirs(data_folder_models)
encoder_path = os.path.join(data_folder_models, "encoder.pkl")


def bug_checker(merged_data):
    
    #determine if the commit-file had a bug
    merged_data['Bug'] = 0
    merged_data.loc[merged_data[BUG_ID_FIELD].notna(), 'Bug'] = 1
    merged_data.loc[merged_data['comment'].str.contains('fix', case=False, na=False), 'Bug'] = 1

    #save information of bugs
    bug_info = {}

    for _, row in merged_data[merged_data['Bug'] == 1].iterrows():
        ticket_id = row[BUG_ID_FIELD]
        creation_date = pd.to_datetime(row['creation']).tz_localize(None)
        update_date = pd.to_datetime(row['update']).tz_localize(None)
        modified_files = row['modified_files']
        if ticket_id not in bug_info:
            bug_info[ticket_id] = {'dates': (creation_date, update_date), 'files': set()}
        bug_info[ticket_id]['files'].add(modified_files)


    def validate_bug_persistence(row, bug_info):
        commit_date = pd.to_datetime(row['date']).tz_localize(None)
        modified_files = row['modified_files']
        for bug_data in bug_info.values():
            creation_date, update_date = bug_data['dates']
            affected_files = bug_data['files']
            if creation_date <= commit_date <= update_date and modified_files in affected_files:
                # if the commit is inside the range of dates of bug and the file is affected, check it as a bug
                return 1
        return row['Bug']  
    
    merged_data['Bug'] = merged_data.apply(lambda row: validate_bug_persistence(row, bug_info), axis=1)

    # Count and print the number of rows with bugs
    bug_count = (merged_data['Bug'] == 1).sum()
    total_rows = len(merged_data)
    print(f"Total rows with bugs: {bug_count} out of {total_rows} ({bug_count/total_rows*100:.2f}%)")

    return merged_data



def generate_author_category_mapping(original_authors, orig_to_unified, contribution_percent):
    """
    Generate CSV mapping of original authors to their categories.
    
    Args:
        original_authors: Series with original author names
        orig_to_unified: Dictionary mapping original to unified names
        contribution_percent: DataFrame with author contribution data
    
    Returns:
        None: Saves CSV file with author mapping
    """
    author_mapping = []
    
    for original_author in original_authors.unique():
        if pd.isna(original_author):
            continue
        
        # Find the unified author name
        unified_author = orig_to_unified.get(original_author, original_author)
        
        # Find the category for this unified author
        author_contrib = contribution_percent[contribution_percent['author'] == unified_author]
        
        if not author_contrib.empty:
            row = author_contrib.iloc[0]
            if row['major_contributor'] == 1:
                category = 'major'
            elif row['minor_contributor'] == 1:
                category = 'minor'
            elif row['sporadic_contributor'] == 1:
                category = 'sporadic'
            else:
                category = 'unknown'
            
            contrib_percent = row['contribution_percent']
        else:
            category = 'unknown'
            contrib_percent = 0
        
        author_mapping.append({
            'original_author': original_author,
            'unified_author': unified_author,
            'category': category,
            'contribution_percent': contrib_percent
        })

    # Create DataFrame and save mapping
    author_mapping_df = pd.DataFrame(author_mapping)
    author_mapping_path = os.path.join(data_folder, 'author_category_mapping.csv')
    author_mapping_df.to_csv(author_mapping_path, index=False)
    print(f"Author category mapping saved in {author_mapping_path}")
    
    return author_mapping_df


def normalization_data(bugeaded_data, mode):
    
    def split_camel_case(text):
        # Separate words in CamelCase: "GabriellaDivine" -> "Gabriella Divine"
        return re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', text)

    # apply function to unify authors
    def unify_author(name):
        if pd.isna(name):
            return 'unknown'
        name = re.sub(r'\bdev\b', '', name, flags=re.IGNORECASE)
        name = ' '.join(split_camel_case(word) for word in name.split())
        name = unidecode.unidecode(name).lower().strip()
        tokens = re.findall(r'\w+', name)
        tokens = sorted(tokens)
        return ' '.join(tokens)

    # Store original authors before normalization
    original_authors = bugeaded_data['author'].copy()
    
    authors_norm = bugeaded_data['author'].apply(unify_author)

    # Fuzzy matching
    unique_authors = authors_norm.unique()
    author_map = {}
    for author in unique_authors:
        if author in author_map:
            continue
        matches = process.extract(author, unique_authors, scorer=fuzz.ratio, score_cutoff=90)
        for match, score, _ in matches:
            author_map[match] = author

    # Mapping names to fuzzy ones
    orig_to_unified = dict(zip(bugeaded_data['author'], authors_norm.map(author_map)))

    # author unified
    bugeaded_data['author'] = bugeaded_data['author'].map(orig_to_unified)
    
    if mode == 'train':
        # generation of percentage contribution of each developer BY COMMITS
        commit_counts = bugeaded_data.groupby('author')['commit_id'].nunique()
        total_commits = bugeaded_data['commit_id'].nunique()
        contribution_percent = (commit_counts / total_commits).reset_index()
        contribution_percent.columns = ['author', 'contribution_percent']

        contribution_percent['major_contributor'] = (contribution_percent['contribution_percent'] > THRESHOLD_CONTRIB_HIGH).astype(int) 
        contribution_percent['minor_contributor'] = ((contribution_percent['contribution_percent'] > THRESHOLD_CONTRIB_LOW) & 
        (contribution_percent['contribution_percent'] <= THRESHOLD_CONTRIB_HIGH)).astype(int) 
        contribution_percent['sporadic_contributor'] = (contribution_percent['contribution_percent'] <= THRESHOLD_CONTRIB_LOW).astype(int)

        contribution_percent_path = os.path.join(data_folder, 'contribution_percent.csv')
        contribution_percent.to_csv(contribution_percent_path, index=False)
        print(f"Percentage of contribution by commits saved in {contribution_percent_path}")

        # Generate author category mapping using the new function
        generate_author_category_mapping(original_authors, orig_to_unified, contribution_percent)

        cats = contribution_percent.set_index('author')[['major_contributor', 'minor_contributor', 'sporadic_contributor']] 
        bugeaded_data = bugeaded_data.join(cats, on='author')

               
    else:
        # load contribution percent data
        contribution_percent_path = os.path.join(data_folder, 'contribution_percent.csv')
        contribution_percent = pd.read_csv(contribution_percent_path)
        
        cats = contribution_percent.set_index('author')[['major_contributor', 'minor_contributor', 'sporadic_contributor']] 
        bugeaded_data = bugeaded_data.join(cats, on='author')        


    bugeaded_data[['major_contributor', 'minor_contributor', 'sporadic_contributor']] = ( 
        bugeaded_data[['major_contributor', 'minor_contributor', 'sporadic_contributor']] .fillna(0) .astype('int8') )

    bugeaded_data.drop(columns=['author'], inplace=True)

    #other columns (numeric)
    others_columns = [col for col in bugeaded_data.columns if col not in selected_text_cols] #columns_to_escale +

    # Codify columns categoric/text
    if mode == 'train':
        encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
        text_data_encoded = encoder.fit_transform(bugeaded_data[selected_text_cols])
        text_data_encoded_df = pd.DataFrame(text_data_encoded, columns=encoder.get_feature_names_out(selected_text_cols), index=bugeaded_data.index)
        joblib.dump(encoder, encoder_path)
    else:
        # Load the encoder trained during training
        encoder = joblib.load(encoder_path)
        text_data_encoded = encoder.transform(bugeaded_data[selected_text_cols])
        text_data_encoded_df = pd.DataFrame(text_data_encoded, columns=encoder.get_feature_names_out(selected_text_cols), index=bugeaded_data.index)


    others_columns_df = bugeaded_data[others_columns]

    # save DataFrame combined in CSV
    full_data_path = os.path.join(data_folder_preprocess, 'full_data_set.csv')
    bugeaded_data.to_csv(full_data_path, index=False)
    print(f"Dataframe with contributoirs and categoric columns saved in {full_data_path}")

    data_scaled = pd.concat([text_data_encoded_df, others_columns_df], axis=1)
    
    print("Shape after scaling categoric columns:", data_scaled.shape)
    
    # Remove rows where file_name column is empty --> are files that now do not exist
    if 'file_name' in data_scaled.columns:
        empty_file_name_count = data_scaled['file_name'].isna().sum()
        if empty_file_name_count > 0:
            print(f"Removing {empty_file_name_count} rows with empty file_name")
            data_scaled = data_scaled.dropna(subset=['file_name'])
       
    
    # Updated columns to drop (not useful for training)
    columns_to_drop = COLUMNS_TO_DROP
     
    data_scaled = data_scaled.drop(columns=columns_to_drop, errors='ignore')
    
    # save DataFrame scaled in CSV
    data_scaled_path = os.path.join(data_folder_preprocess, 'scaled_data_set.csv')
    data_scaled.to_csv(data_scaled_path, index=False)

    print(f"Data concatenated and cleaned saved in {data_scaled_path}")

    
    # Extract names of files
    unique_file_names = data_scaled['file_name_commit'].dropna().unique()

    
    if mode == 'train':

        hashes_df = pd.DataFrame(unique_file_names, columns=["file_name_unique"])
        # Generate hashes for each file and store them in a new column
        hashes_df["file_hash"] = hashes_df["file_name_unique"].apply(lambda x: int(hashlib.md5(x.encode()).hexdigest(), 16))% (10**12)

        # Convert the column to numeric type before merging
        hashes_df["file_hash"] = pd.to_numeric(hashes_df["file_hash"], errors="coerce")
            
        # backup file hashes
        hashes_backup_path = os.path.join(data_folder, 'file_hashes_backup.csv')
        hashes_df.to_csv(hashes_backup_path, index=False)
        print(f"File hashes backup saved in {hashes_backup_path}")

    else:
        if mode == 'predict':
            # load final dataset to get file hashes
            hashes_df_path = os.path.join(data_folder, 'file_hashes_backup.csv')
            hashes_df = pd.read_csv(hashes_df_path)

    # Merge the hashes back into the main dataset       
    final_dataset = data_scaled.merge(hashes_df, left_on="file_name_commit", right_on="file_name_unique", how="left")
    

    # Check for any missing hashes after the merge
    missing_hashes = final_dataset['file_hash'].isna().sum()
    if missing_hashes > 0:
        print(f"Warning: There are {missing_hashes} rows with missing file hashes after merging.")

        
    # Eliminate original columns from dataset
    final_dataset = final_dataset.drop(columns=['modified_files', 'file_name_unique', 'location', 'file_name_commit'], errors='ignore')

    # Feature validation and alignment for prediction mode
    if mode == 'predict':
        # Load training features order and names
        training_features_path = os.path.join(data_folder, 'training_features.csv')
        
        if os.path.exists(training_features_path):
            training_features_df = pd.read_csv(training_features_path)
            training_features = training_features_df['feature_name'].tolist()
                                  
            # Get current features
            current_features = final_dataset.columns.tolist()
            
            # Find missing features
            missing_features = set(training_features) - set(current_features)
            extra_features = set(current_features) - set(training_features)
            
            if missing_features:
                print(f"Adding {len(missing_features)} missing features filled with zeros")
                for feature in missing_features:
                    final_dataset[feature] = 0
            
            if extra_features:
                print(f"Removing {len(extra_features)} extra features not present in training")
                final_dataset = final_dataset.drop(columns=list(extra_features))
            
            # Reorder columns to match training order
            final_dataset = final_dataset.reindex(columns=training_features, fill_value=0)
            
            print(f"Features aligned. Final feature count: {len(final_dataset.columns)}")
                       
            
        else:
            print(f"Warning: Training features file not found at {training_features_path}")
            print("Cannot validate feature alignment for prediction mode")
    
    elif mode == 'train':
        # Save training features order for future prediction validation
        training_features = final_dataset.columns.tolist()
        training_features_df = pd.DataFrame({'feature_name': training_features})
        training_features_path = os.path.join(data_folder, 'training_features.csv')
        training_features_df.to_csv(training_features_path, index=False)
        print(f"Training features saved to {training_features_path}")
        print(f"Total training features: {len(training_features)}")


    # If there are NaN values, fill them
    final_nan_count = final_dataset.isna().sum().sum()
    if final_nan_count > 0:
        # print(f"\nFilling remaining {final_nan_count} NaN values with zeros...")
        final_dataset = final_dataset.fillna(0)
        # print("✓ All NaN values filled with zeros")
        
        
    #save the final set
    final_data_set_path = os.path.join(data_folder_preprocess, 'final_dataset_complete.csv')
    final_dataset.to_csv(final_data_set_path, index=False)
    print(f"Dataset completed in {final_data_set_path}")

    return final_dataset