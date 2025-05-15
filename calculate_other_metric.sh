#!/bin/bash

# Define ranges for top_ep and top_ep_tm
top_ep_values=(0.95 0.99)

top_ep_tm_values=(1.0 2.0 1.1 1.5 2.5 3.0 3.5 4.0)



# SLURM parameters
data_dir="data/webtext/"
model_name="meta-llama/Llama-2-7b-hf"
datasplit="test"
generate_seed=0
seed=1234
device=0
generation_type="basic"

# File path where the generated files will be saved (adjust as necessary)
output_directory="outputs/webtext_${model_name}/metrics/basic/"  # Define the folder where your outputs are stored

# Loop through different values of top_ep and top_ep_tm
for top_ep in "${top_ep_values[@]}"; do
    for top_ep_tm in "${top_ep_tm_values[@]}"; do

        # File to check before submitting the job
        output_file="${output_directory}all_L_test_p1.0_k0_t1.0_ep${top_ep}_tm${top_ep_tm}_seed0.p"

        # Check if the file already exists
        if [[ -f "${output_file}" ]]; then
            echo "File ${output_file} already exists. Skipping submission."
        else
            # Submit the job with the current top_ep and top_ep_tm if the file does not exist
            sbatch run_all_metrics.slurm \
                --data_dir ${data_dir} \
                --model_name ${model_name} \
                --datasplit ${datasplit} \
                --generate_seed ${generate_seed} \
                --seed ${seed} \
                --device ${device} \
                --generation_type ${generation_type} \
                --top_ep ${top_ep} \
                --top_ep_tm ${top_ep_tm}

            echo "Submitted job with top_ep=${top_ep} and top_ep_tm=${top_ep_tm}"
        fi
    done
done

top_p_values=(0.0 0.9 0.95 0.99 1.0)

# Loop through different values of top_p
for top_p in "${top_p_values[@]}"; do

    # File to check before submitting the job
    output_file="${output_directory}all_L_test_p${top_p}_k0_t1.0_ep1.0_tm1.0_seed0.p"

    # Check if the file already exists
    if [[ -f "${output_file}" ]]; then
        echo "File ${output_file} already exists. Skipping submission."
    else
        # Submit the job with the current top_p if the file does not exist
        sbatch run_all_metrics.slurm \
            --data_dir ${data_dir} \
            --model_name ${model_name} \
            --datasplit ${datasplit} \
            --generate_seed ${generate_seed} \
            --seed ${seed} \
            --device ${device} \
            --generation_type ${generation_type} \
            --top_p ${top_p}

        echo "Submitted job with top_p=${top_p}"
    fi
done
