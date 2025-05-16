# Decoding Game Experiments Repository

This repository is adapted from the MAUVE experiments repository:

* [MAUVE Repository](https://github.com/krishnap25/mauve-experiments)

## Supported Models

You can run the experiments using any of the following models:

* GPT-2 Series: `"gpt2"`, `"gpt2-large"`, `"gpt2-medium"`, `"gpt2-xl"`
* Meta Llama: `"meta-llama/Llama-2-7b-hf"`
* EleutherAI GPT-J: `"EleutherAI/gpt-j-6B"`

## Steps to Run the Experiments

### 1. Setup Output Directories

Run the following script to set up the output directories:

```bash
bash make_output_dirs.sh
```

### 2. Featurize Human-Written Text

Use the following command to featurize the human-written text:

```bash
sbatch run_ref.slurm --data_dir data/webtext/ --model_name 'gpt2-large' --seed 0 --datasplit test --use_large_feats --device 0 --featurize_model_name 'gpt2-large' --max_len 256
```

### 3. Compute Perplexity and Repetition (Human Text)

```bash
sbatch run_all_metrics_ref.slurm --data_dir data/webtext/ --model_name 'gpt2-large' --datasplit test --device 0
```

### 4. Generate Text with Decoding Methods

* Run `compute_generation.sh` to generate text using Game Sampling and Nucleus Sampling.

* For other methods, use the following commands:

  * **Pure Sampling:**

    ```bash
    sbatch run_generations.slurm --data_dir data/webtext/ --model_name 'gpt2-large' --seed 0 --prompt_size 35 --datasplit test --use_large_feats --device 0 --max_len 256
    ```

  * **Greedy Decoding:**

    ```bash
    sbatch run_generations.slurm --data_dir data/webtext/ --model_name 'gpt2-large' --seed 0 --prompt_size 35 --top_p 0.0 --datasplit test --use_large_feats --device 0 --max_len 256
    ```

  * **Contrastive Search:**

    ```bash
    sbatch run_generations.slurm --data_dir data/webtext/ --model_name 'gpt2-large' --seed 0 --prompt_size 35 --cs_alpha 0.6 --datasplit test --use_large_feats --device 0 --max_len 256
    ```

  * **Typical Sampling:**

    ```bash
    sbatch run_generations.slurm --data_dir data/webtext/ --model_name 'gpt2-large' --seed 0 --prompt_size 35 --typical_p 0.9 --datasplit test --use_large_feats --device 0 --max_len 256
    ```

### 5. Calculate MAUVE Scores (Generated Text)

```bash
bash calculate_mauve.sh
```

### 6. Compute Repetition and Perplexity (Generated Text)

```bash
bash calculate_other.sh
```

### 7. Generate Result Tables

Specify the model in `generate_tables.py` and run it to produce the output tables.

### Note

* The main algorithm for the decoding game can be found in `src/model_utils.py`.
