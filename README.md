# MonoProof

This is the github repo for Tool MonoProof. MonoProof supports the proof of unsatisfiability for finite
domain monotonic theories, including:

1. Graph Reachability
2. Bit-vector summation and comparison
3. Maximum Flow
4. Graph cyclicity (incomplete)
5. PB constraints (incomplete)

## Installation

### 1. Install MonoSAT with proof support:
```
    git clone https://github.com/NickF0211/monosat
    cd {monosat_dir}
    git checkout proof_of_unsat
```

Please follow MonoSAT's installation instruction to build MonoSAT

add monosat executable location to `monosat_path` in `mono_proof.py` 

### 2. Build drat-trim
    gcc -o drat-trim drat-trim.c
    gcc -o drat-trim-orig drat-trim-orig.c

### 3. Install python dependency
1. pysat: https://pysathq.github.io/installation/
2. pyz3: `pip3 install z3-solver` (testing only)
3. numpy: `pip3 install numpy` (benchmarking only)

## Launch MonoProof

``python3 run_mono_proof.py {input.gnf}``

### Other options:
    --no-backward-check   # Skip theory lemma trimming
    --lemma-bitblast      # Use lemma specific bit-blasting for proof checking instead of Horn approixmation
    --no-witness-reduction  # eager theory axiomatization (for graph reachability only)
    --solver-opt = {options} # options for launch MonoSAT

## Benchmarking:
1. Download Benchmark suits from: https://zenodo.org/records/10530451?token=eyJhbGciOiJIUzUxMiJ9.eyJpZCI6ImVlNWMyOTQ3LWNmNGYtNDNlYi05YmUxLWRiYzk2ZWQyMTBhOCIsImRhdGEiOnt9LCJyYW5kb20iOiI3MWZjYjQ0OGRmYjJlN2U1NjZjYTBlODNjYzQwNTEwMyJ9.i92uMNjWT5qBi4X1CN753M1kdPjRLOHsZlhU71BQ6ksanSrewL_1YZ2iCFof2-KIB_-9pHUAwvIz4HLbr0Lk3g
2. There are two sets of gnfs:
    ```
    unzip key_flow.zip  #Network Reachability UNSAT Benchmark
    unzip BGA_Escape_benchmark.zip # BGA Escape Routing UNSAT Benchmark
    ```
3. Launch benchmark:
   ```
   python3 maxflow_experiment.py     
   python3 reach_exp.py key_flow_simp key_flow.csv
   ```
   The BGA Escape routing results will be saved in `maxflow.csv` and the network reachability results will be saved in `key_flow.csv`.
    

4. Comparing with Bit-Blasting
   1. download and build kissat:
      
      ```
      wget https://github.com/arminbiere/kissat/archive/refs/tags/rel-3.1.1.zip
      unzip rel-3.1.1.zip
      cd kissat-rel-3.1.1
      ./configure && make test 
      ```
    update `solver_path` in `bit_blast.py` to the built kissat executable
   
    2. Launch 
         ```
            python3 maxflow_exp_bitblast.py BGA_Escape_benchmark maxflow_bb.csv #pure bit-blast for BGA
            python3 maxflow_experiment_lsb.py                                   #lemma specific bit-blasting for BGA
            python3 reach_exp_bitblast.py key_flow_simp key_flow_bb.csv         #pure bit-blast for Network
            python3 reach_exp_lsb.py key_flow_simp key_flow_lsb.csv             #lemma specific bit-blasting for Network
            
         ```
         The BGA Escape routing results will be saved in `maxflow_bb.csv` (pure bit-blasting) and  `maxflow_lsb.csv` (lemma-specific bit-blasting)
         The network reachability results will be saved in `key_flow_bb.csv` and `key_flow_lsb.csv` 
