dir = "latestfiles_sep6/"
files= ["hepscore_wl_scores_alice_gen_sim_reco_run3_bmk_gen_sim.txt",      \
        "hepscore_wl_scores_atlas_gen_sherpa_bmk_gen.txt",                 \
        "hepscore_wl_scores_atlas_reco_mt_bmk_reco.txt",                   \
        "hepscore_wl_scores_belle2_gen_sim_reco_2021_bmk_gen_sim_reco.txt",\
        "hepscore_wl_scores_cms_digi_run3_bmk_digi.txt",                   \
        "hepscore_wl_scores_cms_gen_sim_run3_bmk_gen_sim.txt",             \
        "hepscore_wl_scores_cms_reco_run3_bmk_reco.txt",                   \
        "hepscore_wl_scores_lhcb_gen_sim_2021_bmk_sim.txt" ]
nWorkloads = len(files)

# First pass, get CPU models that have every bm
candidates = []
for resfile in files:
    with open(dir+resfile,'r') as f:
        for line in f:
            if "Intel" in line or "AMD" in line:
                candidates.append(line.split()[0])

rejected = []
for candidate in candidates:
    for resfile in files:
        with open(dir+resfile,'r') as f:
            for line in f:
                if candidate not in f.read():
                    rejected.append(candidate)

finalcandidates = []
for candidate in candidates:
    if candidate not in rejected and candidate not in finalcandidates:
    #if candidate not in finalcandidates:
        finalcandidates.append(candidate)

for cand in finalcandidates:
    print(cand)

usedcandidates = []
arch = {}
for candidate in finalcandidates:
    with open(dir + files[0], 'r') as f:
        for line in f:
            if candidate in line and candidate not in usedcandidates:
                usedcandidates.append(candidate)
                if line.split()[1] in arch:
                    arch[line.split()[1]] = arch[line.split()[1]] + 1
                    print(candidate, line.split()[1])
                else:
                    arch[line.split()[1]] = 1
                    print(candidate, line.split()[1])

for key in arch:
    print(key, arch[key])
