import os
import pickle
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.table as tbl

# Define the folder path where the .p files are located

model_name = 'meta-llama/Llama-2-7b-hf'
folder_path = f'outputs/webtext_{model_name}/metrics/basic/'

# Initialize an empty list to store the data
data_all = []
data_mauve= []
# Loop through all files in the folder
for file_name in os.listdir(folder_path):
    # Check if the file is a .p file
    if file_name.endswith('.p'):
        # Extract ep and tm values from the file name (assuming the format remains consistent)
        try:
            parts = file_name.split('_')
            ep_value = parts[6][2:]  # Extract value after 'ep'
            tm_value = parts[7][2:]  # Extract value after 'tm'
            p_value = parts[3][1:] # Extract value after 'p'
            cs_value = parts[8][2:] # Extract value after 'cs'
            typical_value = parts[9][7:] # Extract value after 'typical'
            # Full file path
            file_path = os.path.join(folder_path, file_name)

            # Open the .p file and load its contents
            with open(file_path, 'rb') as file:
                file_data = pickle.load(file)
                if parts[0] == 'all' :
                    # Extract perplexity and repetition from the data
                    perplexity = file_data.get('perplexity', None)
                    repetition = file_data.get('repetition', None)
                    data_all.append({
                        '(Nucleus)p' : p_value, 
                        '(Game)Epsilon': ep_value,
                        '(Game)temp': tm_value,
                        'contrastive': cs_value,
                        'typical' : typical_value,
                        'perplexity': perplexity,
                        'repetition': repetition
                    })            
                if parts[0] == 'mauve' :
                    mauve = file_data[0]
                    data_mauve.append({
                        '(Nucleus)p' : p_value, 
                        '(Game)Epsilon': ep_value,
                        '(Game)temp': tm_value,
                        'contrastive': cs_value,
                        'typical' : typical_value,
                        'MAUVE' : mauve
                    })                    
                    
                # Append the extracted data to the list


        except Exception as e:
            print(f"Error processing {file_name}: {e}")



    

# Convert the list to a DataFrame
df_all = pd.DataFrame(data_all)
df_mauve = pd.DataFrame(data_mauve)
df_merged = pd.merge(df_all, df_mauve, on=['(Nucleus)p', '(Game)Epsilon', '(Game)temp', 'contrastive', 'typical'], how='left')







df_sorted = df_merged.sort_values(by=['MAUVE'], ascending=False)


#df_sorted = df_sorted.round(3)

#df_sorted[['perplexity', 'repetition', 'MAUVE']] = df_sorted[['perplexity', 'repetition', 'MAUVE']].map(
#    lambda x: ('{:.3f}'.format(x)).rstrip('0').rstrip('.') if isinstance(x, (int, float)) else x
#)

#columns_to_drop = ['(Nucleus)p', 'contrastive', 'typical']

#df_sorted = df_sorted.drop(columns=columns_to_drop)

#df_sorted = df_sorted.sort_values(by=['(Game)Epsilon', '(Game)temp'])


latex_table = df_sorted.to_latex(index=False)  # `index=False` removes the index column from the output

# Print the LaTeX code
print(latex_table)
# Display the DataFrame
print(df_sorted)

