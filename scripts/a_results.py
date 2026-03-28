
import numpy as np
import os
from lime.lime_tabular import LimeTabularExplainer
from config import MAX_EXPLANATIONS


# ==============================================================
# LIME (Explicability local) with prioritization on probability
# ==============================================================


def explainability(probabilities_df_unique, file_hashes_df, mode, brf_model, X_train, origin_instance):

    explanations_generated = 0

    explainability_dir = "explainability"
    os.makedirs(explainability_dir, exist_ok=True)

    # Create explainer LIME with all features
    explainer_lime = LimeTabularExplainer(
        training_data=np.array(X_train),  # all features
        mode="classification",
        feature_names=X_train.columns, 
        class_names=["Free Bug", "With Bug"], 
        discretize_continuous=True
    )

    # Iterate on each instance ordered by probability descendent
    for _, row in probabilities_df_unique.iterrows():
        if explanations_generated >= MAX_EXPLANATIONS:
            print((MAX_EXPLANATIONS), "\n explanaitions generated")
            break

        file_hash_value = row['file_hash']    
        probability = row['probability_class_1']  

        if mode == 'predict':   
            prediction = row['prediction']
        
        if mode == 'train':
            instance_index = row['index'] 

        # search the real name of the file in file_hashes_df
        try:
            file_name = file_hashes_df.loc[file_hashes_df['file_hash'] == file_hash_value, 'file_name_unique'].values[0]
        except IndexError:
            file_name = f"Unknown file (file_hash={file_hash_value})" 


        print(f"\nGenerating explainability LIME for file_hash: {file_hash_value} (File: {file_name}, Probability bug: {probability:.2f})")

        # get correspond instance
        if mode == 'predict':
            instance = origin_instance[origin_instance['file_hash'] == file_hash_value].iloc[0]
        elif mode == 'train':
            instance = origin_instance.loc[instance_index]

        
        
        # Generate explainability for instance
        lime_explanation = explainer_lime.explain_instance(
            data_row=instance[X_train.columns].values, 
            predict_fn=brf_model.predict_proba,
            num_features=len(X_train.columns)
        )
        
        # Customize title of HTML with file_hash and real name file
        explanation_html_path = os.path.join(
            explainability_dir, f"lime_explanation_file_hash_{file_hash_value}.html")
        lime_explanation.save_to_file(explanation_html_path)  

        explanation_text_path = os.path.join(
            explainability_dir, f"lime_explanation_file_hash_{file_hash_value}.txt")
        
        with open(explanation_html_path, "r", encoding="utf-8") as file:  
            explanation_html_content = file.read()

        # Replace title <title>
        new_title = f"Prediction probabilities of {file_name}"
        explanation_html_content = explanation_html_content.replace(
            "<title>Lime explanation</title>",
            f"<title>{new_title}</title>"
        )

        # Create a block with customized style
        custom_style = """
        <style>
            /* Ajust wide of subcontainer lime.explanation */
            .lime.explanation {
                max-width: 700px;
                width: 50%;
                margin: auto;
                padding: 10px;
                box-sizing: border-box;
            }

            /* Ajust wide of subcontainer lime table_div */
            .lime.table_div {
                max-width: 700px;
                width: 50%;
                margin: auto;
                padding: 10px;
                box-sizing: border-box;
            }
        </style>
        """

        # Insert the block style in <head> 
        if "<head>" in explanation_html_content:        
            head_end_position = explanation_html_content.find("</head>")
            explanation_html_content = (
                explanation_html_content[:head_end_position] 
                + custom_style  
                + explanation_html_content[head_end_position:]  
            )
        else:
            print("Label <head> not found")

        explanation_html_content = explanation_html_content.replace(
            "<body>",
            f"<body><h1>{new_title}</h1>"
        )

        # save HTML with changes
        with open(explanation_html_path, "w", encoding="utf-8") as file:  
            file.write(explanation_html_content)

        print(f"Explainability LIME saved in HTML {explanation_html_path}")
        
        explanation_as_list = lime_explanation.as_list()
        explanation_text = "\n".join([f"{i+1}. {feature}: {contribution}" for i, (feature, contribution) in enumerate(explanation_as_list)])

        with open(explanation_text_path, "w", encoding="utf-8") as file:
            file.write(explanation_text)

        print(f"Explainability LIME saved in text {explanation_text_path}")
    
        explanations_generated += 1

