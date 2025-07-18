import multiprocessing
import numpy as np
from sage.all import *
from sage.rings.integer import Integer
from tqdm import tqdm
from typing import Dict, List, Optional, Set, Tuple

# Type Aliases
PartitionTuple = Tuple[Integer, int, Integer, int]
PartitionDict = Dict[int, Set[PartitionTuple]]

# Global Sage Primes set object for efficient access.
P = Primes()

def _find_sage_sum_bases(n: Integer) -> Set[PartitionTuple]:
    """
    Finds prime pairs (p, q) and exponents (j, k) such that p^j + q^k = n, where j, k >= 1.
    Takes a prime and returns a set of canonical tuples (prime1, exp1, prime2, exp2) representing
    unique partitions.
    """
    found_tuples: Set[PartitionTuple] = set()

    def get_prime_power_info(val: Integer) -> Optional[Tuple[Integer, int]]:
        if val.is_prime(proof=False):
            return val, 1
        

        base, exponent = val.perfect_power()
        if base.is_prime(proof=False):
            return base, exponent
        return None

    for sum_pair in Partitions(n, length=2):
        e1 = sum_pair[0]
        e2 = sum_pair[1]

        e1_info = get_prime_power_info(e1)
        e2_info = get_prime_power_info(e2)

        if e1_info is None or e2_info is None:
            continue
        
        # Canonical representation
        if e1_info[0] <= e2_info[0]:
            power_tuple = (*e1_info, *e2_info)
        else:
            power_tuple = (*e2_info, *e1_info)
        
        found_tuples.add(power_tuple)

    if not found_tuples:
        found_tuples.add((Integer(0), 0, Integer(0), 0))
    return found_tuples

def _process_batch_from_indices(index_range: Tuple[int, int]) -> PartitionDict:
    """
    Worker function for multiprocessing. Processes a range of primes specified by start and end indices.
    """
    start_idx, end_idx = index_range

    # Determine the actual prime numbers for the range.
    # prime_range is exclusive of the end value.
    start_prime = P.unrank(start_idx)
    # We need the prime *after* our last one to set the upper bound.
    end_prime_exclusive = P.unrank(end_idx + 1)
    
    primes_in_range = prime_range(start_prime, end_prime_exclusive)

    results: PartitionDict = {}
    for n in primes_in_range:
        results[n] = _find_sage_sum_bases(n)
    return results

def generate_partitions(num_primes: int, batch_size: int, num_processes: int, resume: bool, resume_file_path: Optional[str] = None) -> PartitionDict:
    """
    Generates prime power partitions by distributing work to a pool of processes.
    Each worker is given a start and end *index* and is responsible for generating
    the primes for that range. This avoids creating a large list of primes in the main process.
    """

    if num_primes <= 0:
        return {}
    start_idx = 0
    if resume:
        from . import utils
        try:
            # Use provided path or get default data path
            if resume_file_path:
                csv_path = resume_file_path
            else:
                config = utils.get_config()
                csv_path = config.default_data_path
            
            last_prime = utils.get_last_prime(csv_path)
            start_idx = P.rank(last_prime) + 1
            utils.create_backup(csv_path)
            print(f"Resuming from prime {P.unrank(start_idx)} (index {start_idx})")
        except (FileNotFoundError, ValueError) as e:
            print(f"Resume failed: {e}")
            print("Please check the data file path or run without --resume to start fresh.")
            return {}
    
    # Create a generator for the ranges of indices for workers.
    # This avoids materializing a potentially huge list of tasks in memory.
    start_range = list(range(start_idx, start_idx + num_primes, batch_size))
    end_range = list(range(start_idx + batch_size - 1, start_idx + num_primes + batch_size - 1, batch_size))
    index_ranges = zip(start_range, end_range)
    
    master_data_dict: PartitionDict = {}
    
    with multiprocessing.Pool(processes=num_processes) as pool:
        # Calculate total batches for the progress bar without consuming the generator.
        total_batches = (num_primes + batch_size - 1) // batch_size
        
        # Use imap_unordered to process batches as they complete, which is memory-efficient.
        for batch_results in tqdm(pool.imap_unordered(_process_batch_from_indices, index_ranges), total=total_batches, desc="Processing Batches"):
            master_data_dict.update(batch_results)
            
    return master_data_dict
