#!/bin/bash

# Define ranges for top_ep and top_ep_tm
top_ep_values=(0.95 0.99)

top_ep_tm_values=(1.0 2.0 1.1 1.5 2.5 3.0 3.5 4.0)


# SLURM parameters
data_dir="data/webtext/"
model_name="meta-llama/Llama-2-7b-hf"
featurize_model_name="meta-llama/Llama-2-7b-hf"

datasplit="test"
seed=0
use_large_feats="--use_large_feats"
max_len=256
device=0
prompt_size=35

# File path where the generated files will be saved (adjust as necessary)
output_directory="outputs/webtext_${model_name}/generations/basic/"  # Define the folder where your outputs are stored



# Loop through different values of top_ep and top_ep_tm
for top_ep in "${top_ep_values[@]}"; do
    for top_ep_tm in "${top_ep_tm_values[@]}"; do
         # File to check before submitting the job
        output_file="${output_directory}featsL256_test_p1.0_k0_t1.0_ep${top_ep}_tm${top_ep_tm}_seed0.pt"

        # Check if the file already exists
        if [[ -f "${output_file}" ]]; then
            echo "File ${output_file} already exists. Skipping submission."
        else
            # Submit the job with the current top_ep and top_ep_tm
            sbatch run_generations.slurm \
                --data_dir ${data_dir} \
                --model_name ${model_name} \
                --datasplit ${datasplit} \
                --seed ${seed} \
                ${use_large_feats} \
                --max_len ${max_len} \
                --device ${device} \
                --prompt_size=${prompt_size} \
                --top_ep ${top_ep} \
                --top_ep_tm ${top_ep_tm} \
                --featurize_model_name ${featurize_model_name}

            echo "Submitted job with top_ep=${top_ep} and top_ep_tm=${top_ep_tm}"
        fi
    done
done



top_p_values=(0.0 0.9 0.95 0.99 1.0)

# Loop through different values of top_p
for top_p in "${top_p_values[@]}"; do

    # File to check before submitting the job
    output_file="${output_directory}featsL256_test_p${top_p}_k0_t1.0_ep1.0_tm1.0_seed0.pt"

    # Check if the file already exists
    if [[ -f "${output_file}" ]]; then
        echo "File ${output_file} already exists. Skipping submission."
    else
        # Submit the job with the current top_p if the file does not exist
        sbatch run_generations.slurm \
                --data_dir ${data_dir} \
                --model_name ${model_name} \
                --datasplit ${datasplit} \
                --seed ${seed} \
                ${use_large_feats} \
                --max_len ${max_len} \
                --device ${device} \
                --prompt_size=${prompt_size} \
                --top_p ${top_p} \
                --featurize_model_name ${featurize_model_name}

        echo "Submitted job with top_p=${top_p}"
    fi
done


