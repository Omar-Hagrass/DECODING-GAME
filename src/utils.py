import argparse
import numpy as np
import os, time
import json
import random
from tqdm.auto import tqdm as tqdm_original
import torch

from transformers import GPT2LMHeadModel, GPT2Tokenizer
from transformers import RobertaModel, RobertaTokenizer
from transformers import AutoTokenizer, AutoModelForCausalLM


CPU_DEVICE = torch.device('cpu')
tqdm = lambda *args, **kwargs: tqdm_original(
    *args, **kwargs, disable=os.environ.get("DISABLE_TQDM", False))
NEWLINE=198


def make_basic_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--device', type=int,
                        help='choose one of [0, 1, 2, 3] for GPU, or CPU otherwise')
    parser.add_argument('--data_dir', type=str, default='./data')
    parser.add_argument('--ds_name', type=str)
    parser.add_argument('--datasplit', type=str)
    parser.add_argument('--model_name', type=str, default='gpt2')
    parser.add_argument('--featurize_model_name', type=str, default='gpt2-large')
    parser.add_argument('--use_large_feats', action='store_true')
    parser.add_argument('--seed', type=int, default=25041993)
    parser.add_argument('--prefix_len', type=int, default=10)
    parser.add_argument('--max_len', type=int, default=1024)
    parser.add_argument('--max_num_generations', type=int, default=5000)
    parser.add_argument('--prompt_size', type=int, default=10)
    parser.add_argument('--top_p', type=float, default=1.0)
    parser.add_argument('--top_k', type=int, default=0)
    parser.add_argument('--top_ep', type=float, default=1.0)
    parser.add_argument('--top_ep_tm', type=float, default=1.0)
    parser.add_argument('--temp', type=float, default=1.0)
    parser.add_argument('--beam_size', type=int, default=4)
    parser.add_argument('--no_repeat_ngram', type=int, default=0)
    parser.add_argument('--entmax_alpha', type=float, default=1.1)
    parser.add_argument('--cs_alpha', type=float, default=0.0)
    parser.add_argument('--typical_p', type=float, default=1.0)
    return parser

def make_metrics_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--device', type=int, default=-1,
                        help='choose one of [0, 1, 2, 3] for GPU, or CPU otherwise')
    parser.add_argument('--datasplit', type=str)
    parser.add_argument('--ref_name', type=str, help='name of human generations to search for')
    parser.add_argument('--max_len', type=int, default=1024)
    parser.add_argument('--ds_name', type=str)
    parser.add_argument('--max_num_data', type=int, default=5000)
    parser.add_argument('--model_name', type=str, default='gpt2')
    parser.add_argument('--data_dir', type=str, default='./data')
    parser.add_argument('--seed', type=int, default=1234)
    parser.add_argument('--force', action='store_true', help='Redo computation even if it already exists')
    parser.add_argument('--use_large_feats', action='store_true', help='Use feats from gpt2-large if true')
    parser.add_argument('--use_bert_feats', action='store_true', help='Use feats from Roberta-large if true')
    parser.add_argument('--subsample_frac', type=float, default=1.0)
    parser.add_argument('--subsample_seed', type=int)

    ##########################
    # Generation Types Args
    ##########################
    gen_parser = parser.add_argument_group('gen_args', 'Generation Type args')

    gen_parser.add_argument('--generation_type', type=str,
                            choices=['basic', 'regr', 'beam', 'entmax'])
    # basic
    gen_parser.add_argument('--top_k', type=int, default=0)
    gen_parser.add_argument('--top_p', type=float, default=1.0)
    gen_parser.add_argument('--top_ep', type=float, default=1.0)
    gen_parser.add_argument('--top_ep_tm', type=float, default=1.0)
    gen_parser.add_argument('--temp', type=float, default=1.0)
    gen_parser.add_argument('--generate_seed', type=int, default=1)
    # beam
    gen_parser.add_argument('--beam_size', type=int, default=4)
    gen_parser.add_argument('--no_repeat_ngram', type=int, default=0)
    # entmax
    gen_parser.add_argument('--entmax_alpha', type=float, default=1.1)
    gen_parser.add_argument('--cs_alpha', type=float, default=0.0)
    gen_parser.add_argument('--typical_p', type=float, default=1.0)

    ##########################
    # PR Args
    ##########################
    pr_parser = parser.add_argument_group('pr_args', 'Arguments to compute PR metrics')
    pr_parser.add_argument('--discretization', type=str,
                           choices=['kmeans_l1', 'kmeans_l2', 'spv', 'drmm'])
    # kmeans
    pr_parser.add_argument('--kmeans_num_clusters', type=int, default=100)
    pr_parser.add_argument('--kmeans_explained_var', type=float, default=0.99)
    # spv
    pr_parser.add_argument('--spv_num_epochs', type=int, default=160)
    # drmm
    pr_parser.add_argument('--drmm_num_epochs', type=int, default=20)
    pr_parser.add_argument('--drmm_n_layer', type=int, default=3)
    pr_parser.add_argument('--drmm_n_component_per_layer', type=int, default=10)

    ##########################
    # Bleu args
    ##########################
    bleu_parser = parser.add_argument_group('bleu_args')
    bleu_parser.add_argument('--n_sample_bleu', type=int, default=500,
                             help='how many sentences to sample to calculate self-bleu')
    bleu_parser.add_argument('--parallel_bleu', action='store_true', help='run in parallel')
    bleu_parser.add_argument('--n_proc_bleu', default=6, type=int)

    return parser

def get_save_filename_from_args(args):
    if args.generation_type == 'basic':
        folder = 'basic'
        filename =  f'{args.datasplit}_p{args.top_p}_k{args.top_k}_t{args.temp}_ep{args.top_ep}_tm{args.top_ep_tm}_cs{args.cs_alpha}_typical{args.typical_p}_seed{args.generate_seed}'
    elif args.generation_type == 'beam':
        folder = 'beam'
        filename = f'{args.datasplit}_b{args.beam_size}_t{args.temp}_nr{args.no_repeat_ngram}_seed{args.generate_seed}'
    elif args.generation_type == 'entmax':
        folder = 'entmax'
        filename = f'{args.datasplit}_entmax{args.entmax_alpha}_seed{args.generate_seed}'
    else:
        raise ValueError('Unknown generation type', args.generation_type)
    print('folder, filename:', (folder, filename))
    return folder, filename

def split_dataset(ds, split_point=500, seed=0):
    rng = random.Random(seed)
    rng.shuffle(ds)
    return ds[:split_point], ds[split_point:]

def get_device_from_arg(device_id):
    if (device_id is not None and
            torch.cuda.is_available() and
            0 <= device_id < torch.cuda.device_count()):
        return torch.device(f'cuda:{device_id}')
    else:
        return CPU_DEVICE

def get_model_and_tokenizer(model_name='gpt2', device=CPU_DEVICE):
    if 'gpt3' in model_name: # For GPT-3 evals, use GPT-2 large
        model_name = 'gpt2-large'
    if 'gpt2' in model_name:
        tokenizer = GPT2Tokenizer.from_pretrained(model_name)
        tokenizer.pad_token_id = tokenizer.eos_token_id
        model = GPT2LMHeadModel.from_pretrained(model_name, pad_token_id=tokenizer.eos_token_id).to(device)
        model = model.eval()
    elif 'meta-llama' in model_name:
        
        '''
        tokenizer = AutoTokenizer.from_pretrained(
            model_name, trust_remote_code=True, padding_side="left"
        )
        
        tokenizer.pad_token = tokenizer.bos_token
        
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            trust_remote_code=True,
        )
        model.config.pad_token_id = model.config.bos_token_id
        model.eval()
        '''

        # Load the tokenizer
        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True,  padding_side="left"  # Enables loading custom Llama architecture
        )
        
        
     
        tokenizer.pad_token = "[PAD]"
        tokenizer.pad_token_id = tokenizer.convert_tokens_to_ids("[PAD]")
        
        
        
        # Load the model
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.bfloat16,      # Automatically choose the best dtype
            device_map="auto",       # Automatically place model on the appropriate device
            low_cpu_mem_usage=True,  # Efficiently load the model
            trust_remote_code=True   # For custom model definitions
        )
        model.config.pad_token_id = tokenizer.pad_token_id
        # Ensure the model is in evaluation mode
        model.eval()
        
        print(f"Padding side: {tokenizer.padding_side}")
        print(f"Pad token ID: {tokenizer.pad_token_id}")
        
    elif 'roberta' in model_name:
        tokenizer = RobertaTokenizer.from_pretrained(model_name)
        model = RobertaModel.from_pretrained(model_name)
    else:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float16).to(device)
        model.config.pad_token_id = tokenizer.eos_token_id
        model = model.eval()
    return model, tokenizer


def get_dataset_name_from_datapath(datapath):
    known_datasets = ['gpt2_output_dataset', 'webtext', 'wp', 'grover']
    transform = {'grover': 'grover', 'webtext': 'webtext', 'wp': 'writingPrompts',
                 'gpt2_output_dataset':'gpt2_output_dataset'}
    for ds_name in known_datasets:
        if transform[ds_name].lower() in datapath.lower():
            return ds_name
    raise ValueError('Unknown dataset', datapath)


def get_model_basename(model_name):
    if 'gpt2-large' in model_name:
        return 'gpt2-large'
    elif 'gpt2-xl' in model_name:
        return 'gpt2-xl'
    elif 'gpt2-medium' in model_name:
        return 'gpt2-medium'
    elif 'gpt2' in model_name:
        return 'gpt2'
    elif 'gpt3-ada' in model_name:
        return 'gpt3-ada'
    elif 'gpt3-babbage' in model_name:
        return 'gpt3-babbage'
    elif 'gpt3-curie' in model_name:
        return 'gpt3-curie'
    elif 'gpt3-davinci' in model_name:
        return 'gpt3-davinci'
    elif 'meta-llama' in model_name:
        return model_name
    else:
        return model_name

def load_json_dataset(data_dir, dataset_name, split=None, max_num_data=np.inf):
    if split is None:
        path = os.path.join(data_dir, f'{dataset_name}.jsonl')
    else:
        path = os.path.join(data_dir, f'{dataset_name}.{split}.jsonl')
    texts = []
    for i, line in enumerate(open(path)):
        if i >= max_num_data:
            break
        texts.append(json.loads(line)['text'])
    return texts

def load_and_tokenize_data(tokenizer, data_dir, max_len, max_num_data, min_len=None, ds_name=None, split='valid'):
    assert max_len <= 1024 and max_num_data >= 2000, f"max_len={max_len}, max_num_data={max_num_data} are insufficient"
    t1 = time.time()
    if ds_name is None:
        ds_name = get_dataset_name_from_datapath(data_dir)
    texts = load_json_dataset(data_dir, ds_name, split=split, max_num_data=max_num_data)
    t2 = time.time()
    print(f'Dataset load time: {round(t2 - t1, 2)} seconds')
    
    # Tokenize the dataset in batches
    t1 = time.time()
    tokenized_texts = tokenizer(
        texts,
        return_tensors="pt",
        truncation=True,
        max_length=max_len,
        padding=True,  # Ensures consistent padding across all inputs
        add_special_tokens=True
    )

    # Ensure minimum length by padding further if needed
    if min_len is not None:
        assert 0 <= min_len <= 100, f"min_len must be between 0 and 100, got {min_len}"

        input_ids = tokenized_texts["input_ids"]
        attention_mask = tokenized_texts["attention_mask"]

        # Determine additional padding required
        current_lengths = input_ids.size(1)
        if current_lengths < min_len:
            pad_length = min_len - current_lengths
            padding_value = tokenizer.pad_token_id

            if tokenizer.padding_side == "right":
                input_ids = torch.nn.functional.pad(input_ids, (0, pad_length), value=padding_value)
                attention_mask = torch.nn.functional.pad(attention_mask, (0, pad_length), value=0)
            elif tokenizer.padding_side == "left":
                input_ids = torch.nn.functional.pad(input_ids, (pad_length, 0), value=padding_value)
                attention_mask = torch.nn.functional.pad(attention_mask, (pad_length, 0), value=0)
            else:
                raise ValueError(f"Unsupported padding_side: {tokenizer.padding_side}")

        tokenized_texts["input_ids"] = input_ids
        tokenized_texts["attention_mask"] = attention_mask

    t2 = time.time()
    print(f'Tokenizing time: {round(t2 - t1, 2)} seconds')

    return tokenized_texts









def load_and_tokenize_data_saved2(tokenizer, data_dir, max_len, max_num_data, min_len=None, ds_name=None, split='valid'):
    assert max_len <= 1024 and max_num_data >= 2000, f"max_len={max_len}, max_num_data={max_num_data} are insufficient"
    t1 = time.time()
    if ds_name is None:
        ds_name = get_dataset_name_from_datapath(data_dir)
    texts = load_json_dataset(data_dir, ds_name, split=split, max_num_data=max_num_data)
    t2 = time.time()
    print(f'Dataset load time: {round(t2 - t1, 2)} seconds')

    # Tokenize the dataset in batches
    t1 = time.time()
    if min_len is None:
        tokenized_texts = tokenizer(
            texts,
            return_tensors="pt",
            truncation=True,
            max_length=max_len,
            padding=True,  # Ensures consistent padding across all inputs
            add_special_tokens=True
        )
    else:
        assert 0 <= min_len <= 100
        tokenized_texts = tokenizer(
            texts,
            return_tensors="pt",
            truncation=True,
            max_length=max_len,
            padding=True,
            add_special_tokens=True
        )
        
        # Adjust tokens for minimum length if needed
        input_ids = tokenized_texts["input_ids"].tolist()
        for i in range(len(input_ids)):
            if len(input_ids[i]) < min_len:
                num_tokens_to_append = min_len - len(input_ids[i])
                input_ids[i].extend([tokenizer.pad_token_id] * num_tokens_to_append)
        
        tokenized_texts["input_ids"] = torch.tensor(input_ids)

    t2 = time.time()
    print(f'Tokenizing time: {round(t2 - t1, 2)} seconds')

    return tokenized_texts






def load_and_tokenize_data_saved(tokenizer, data_dir, max_len, max_num_data, min_len=None, ds_name=None, split='valid'):
    assert max_len <= 1024 and max_num_data >= 2000, f"max_len={max_len}, max_num_data={max_num_data} are insufficent"
    t1 = time.time()
    if ds_name is None:
        ds_name = get_dataset_name_from_datapath(data_dir)
    texts = load_json_dataset(data_dir, ds_name, split=split, max_num_data=max_num_data)
    t2 = time.time()
    print(f'dataset load time: {round(t2-t1, 2)}')
    t1 = time.time()
    if min_len is None:
        tokenized_texts = [tokenizer.encode(sen, return_tensors='pt', truncation=True, max_length=max_len)
                          for sen in texts]
    else:
        assert 0 <= min_len <= 100
        tokenized_texts = [tokenizer.encode(sen, truncation=True, max_length=max_len)
                           for sen in texts]
        # append with newline if necessary
        for i in range(len(tokenized_texts)):
            if len(tokenized_texts[i]) < min_len:
                num_tokens_to_append = min_len - len(tokenized_texts[i])
                tokenized_texts[i].extend([NEWLINE] * num_tokens_to_append)
        tokenized_texts = [torch.LongTensor(sen).unsqueeze(0) for sen in tokenized_texts]

    t2 = time.time()
    print(f'tokenizing time: {round(t2-t1, 2)}')
    return tokenized_texts



def decode_samples_from_lst(tokenizer, lst):
    t1 = time.time()
    # Use batch decoding for better performance
    output = tokenizer.batch_decode(lst, skip_special_tokens=True)
    t2 = time.time()
    print(f'De-tokenizing time: {round(t2-t1, 2)}')
    return output


def decode_samples_from_lst_saved(tokenizer, lst):
    t1 = time.time()
    output = []
    for l in lst:
        o = tokenizer.decode(torch.LongTensor(l), skip_special_tokens=True)
        output.append(o)
    t2 = time.time()
    print(f'de-tokenizing time: {round(t2-t1, 2)}')
    return output





# def shift_hidden_state(hs):
#     # shift hidden state up so that hs[i] corresponds to what was seen before logits[i]
#     n = hs.shape[1]
#     hs = hs.squeeze(0)  # (n, dim)
#     hs2 = hs.clone()
#     hs2[1:n] = hs[0:n-1]
#     hs2[0] = 0  # initial hidden state
#     return hs2[None]  # (1, n, dim)


