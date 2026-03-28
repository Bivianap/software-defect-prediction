import pandas as pd
import os
import ast
from config import COMMIT_PATH_FIELD, BUG_ID_FIELD
   

# This file makes the merges between commits, metrics code and bugs
###############################################################
pk_commit = 'tool_ticket_commit'
pk_metric = 'file_name'  

def perform_merge(commit_data, bugs_data, metrics_data, mode):
    
    #First merge
    combined_data = pd.merge(commit_data, bugs_data, left_on=pk_commit, right_on=BUG_ID_FIELD, how='left')
    print("Rows after first merge (commit_data + issue_data):", combined_data.shape[0])

    # path
    data_folder = os.path.join("..", "data", "preprocess")
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)

    if mode == 'train':        
        # save DataFrame combined in CSV
        combined_data_path = os.path.join(data_folder, '01_preprocess_data.csv')
        combined_data.to_csv(combined_data_path, index=False)

        print(f"File saved with the first merge done in {combined_data_path}")

    if mode == 'predict':        
        # save DataFrame combined in CSV
        combined_data_path = os.path.join(data_folder, 'merge1_predict.csv')
        combined_data.to_csv(combined_data_path, index=False)

        print(f"File saved with the first merge done for prediction in {combined_data_path}")


    # expand the rows
    def expand_rows(row):
        modified_files_raw = row[COMMIT_PATH_FIELD]
        
        # Parse the data
        if pd.isnull(modified_files_raw) or isinstance(modified_files_raw, float):
            modified_files = [None]
        elif isinstance(modified_files_raw, str):
            try:
                modified_files = ast.literal_eval(modified_files_raw)
            except (ValueError, SyntaxError):
                modified_files = [None]
        else:
            modified_files = modified_files_raw
        
        # Check if it's an empty list - if so, skip this row
        if isinstance(modified_files, list) and len(modified_files) == 0:
            return []
            
        expanded_rows = []
        
        # Expand each file in the list
        for file_info in modified_files:
            new_row = row.copy()
            if isinstance(file_info, dict) and 'path' in file_info:
                full_path = file_info['path']
                # Normalize path separators (convert \ to /)
                normalized_path = full_path.replace('\\', '/')
                new_row[COMMIT_PATH_FIELD] = normalized_path
                # DON'T create file_name field - let it come from metrics data only
            elif isinstance(file_info, str):
                # If file_info is just a string path
                normalized_path = file_info.replace('\\', '/')
                new_row[COMMIT_PATH_FIELD] = normalized_path
                # DON'T create file_name field - let it come from metrics data only
            
            expanded_rows.append(new_row)
            
        return expanded_rows

    # Apply the function to each row and generate a new DataFrame
    all_expanded_rows = []
    for _, row in combined_data.iterrows():
        expanded_rows = expand_rows(row)
        all_expanded_rows.extend(expanded_rows)
    
    if not all_expanded_rows:
        print("Warning: No rows were expanded. Check your data format.")
        return pd.DataFrame()
        
    expanded_df = pd.DataFrame(all_expanded_rows)
    expanded_df['file_name_commit'] = expanded_df[COMMIT_PATH_FIELD].apply(
        lambda x: os.path.basename(x) if isinstance(x, str) else None
    )
    print("Rows after expanding lines:", expanded_df.shape[0])

    if mode == 'train':
        expanded_df.to_csv(os.path.join(data_folder,'02_commit_splitting.csv'), index=False)
        print(f"Data splitted saved in commit_splitting.csv")
    
    if mode == 'predict':
        expanded_df.to_csv(os.path.join(data_folder,'02_commit_splitting_for predict.csv'), index=False)
        print(f"Data splitted saved in 02_commit_splitting_for predict.csv")
        
    # Second merge with metrics data using full path
    merged_data = pd.merge(expanded_df, metrics_data, 
                             left_on='file_name_commit', 
                             right_on=pk_metric, 
                             how='left')
    
    # Identify duplicates in file names of metrics_data
    duplicated_file_names = metrics_data[pk_metric][metrics_data[pk_metric].duplicated(keep=False)]

    # Separate rows of expanded_df into unique and duplicated (in the context of metrics_data)
    mask_duplicated = expanded_df['file_name_commit'].isin(duplicated_file_names)
    df_needs_full_path = expanded_df[mask_duplicated]
    df_ok = expanded_df[~mask_duplicated]

    # Merge by name for unique ones
    merged_unique = pd.merge(
        df_ok,
        metrics_data,
        left_on='file_name_commit',
        right_on=pk_metric,
        how='left',
        suffixes=('', '_metrics')
    )

    # Merge by full path for duplicates
    merged_by_path = pd.merge(
        df_needs_full_path,
        metrics_data,
        left_on=COMMIT_PATH_FIELD,
        right_on='location',
        how='left',
        suffixes=('', '_metrics')
    )

    # Combine both results
    merged_data = pd.concat([merged_unique, merged_by_path], ignore_index=True)


    merged_data.to_csv(os.path.join(data_folder,'03_merged_data.csv'), index=False)
    print(f"File saved with the second merge done in {os.path.join(data_folder,'03_merged_data.csv')}")

    print("Merged data columns:", merged_data.columns.tolist())

    return merged_data

###############################################################