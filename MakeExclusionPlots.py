"""
This script plots a version of HS against another version of HS. The main purpose
of it is to test the effect of excluding workloads from HS. It automatically calculates
weights for a given set of workloads, which is a bit more complicated than you might think.
Once it reads in the benchmark scores, there are three functions defined after that: 
one to calculate the weights given a set of workloads, one to calculate the scores given a
set of weights, and one to make the plots given a set of scores.
"""

import array as arr
import ROOT
from ROOT import TCanvas, TH1F, TH2F, TFile, TF1, TPad, TGraphErrors, TLine, TLegend, TLatex, TGraph, TPaveText
from ROOT import gROOT, gStyle, gPad, gApplication

# workloads in alphabetical order
dir = "latestfiles_sep6/"
files= ["hepscore_wl_scores_alice_gen_sim_reco_run3_bmk_gen_sim.txt",      \
        "hepscore_wl_scores_atlas_gen_sherpa_bmk_gen.txt",                 \
        "hepscore_wl_scores_atlas_sim_mt_bmk_sim.txt",                     \
        "hepscore_wl_scores_atlas_reco_mt_bmk_reco.txt",                   \
        "hepscore_wl_scores_belle2_gen_sim_reco_2021_bmk_gen_sim_reco.txt",\
        "hepscore_wl_scores_cms_digi_run3_bmk_digi.txt",                   \
        "hepscore_wl_scores_cms_gen_sim_run3_bmk_gen_sim.txt",             \
        "hepscore_wl_scores_cms_reco_run3_bmk_reco.txt",                   \
        "hepscore_wl_scores_igwn_pe_bmk_pe.txt",                           \
        "hepscore_wl_scores_juno_gen_sim_reco_bmk_gen_sim_reco.txt",       \
        "hepscore_wl_scores_lhcb_gen_sim_2021_bmk_sim.txt" ]
nWorkloads = len(files)

# titles
titles = ["alice", "atlas_gen", "atlas_sim", "atlas_reco", "belle2",\
          "cms_digi", "cms_gen_sim", "cms_reco", "gw", "juno", "lhcb" ]

# read data and fill array with (cpulabel and norm-workload)
workloadCPU =  [[] for i in range(len(files))]
workloadBmk =  [[] for i in range(len(files))]
for i in range(nWorkloads):
    with open(dir+files[i],'r') as f:
        for line in f:
            if "Intel" in line or "AMD" in line:
                line     = line.strip('\n')
                linelist = line.split()
                cpuLabel = linelist[0]+"-"+linelist[3]+"cores-HT"+linelist[4]+"-"+linelist[2]
                workloadCPU[i].append( cpuLabel )
                workloadBmk[i].append( linelist[10] )

# list of all unique CPU-systems
cpuList = []
for i in range(nWorkloads):
    for j in range(len(workloadCPU[i])):
        if not (workloadCPU[i][j] in cpuList):
            # To have only new architectures
            #if "Gold" in workloadCPU[i][j] or "Silver" in workloadCPU[i][j] or "AMD" in workloadCPU[i][j]:
            #    cpuList.append( workloadCPU[i][j] )
            cpuList.append( workloadCPU[i][j] )

# list of the list of workload benchmarks for each unique CPU-system
bmkList =  []
for cpu in cpuList:
    wArray = [0 for i in range(nWorkloads)]
    for i in range(len(files)):
        for j in range(len(workloadCPU[i])):
            if workloadCPU[i][j] == cpu:
                wArray[i] = workloadBmk[i][j]
    bmkList.append( wArray )

def CalculateWeights(WL_list):
    if not isinstance(WL_list, list):
        print("Calculate_weights called without list argument!")
        return -1

    explist = ["atlas", "belle2", "alice", "cms", "lhcb", "gw", "juno"]

    weights = {}

    weights["grid"] = {}
    weights["exp"] = {}
    weights["nom"] = {}

    expnum = 0
    atlasnum = 0
    cmsnum = 0

    share = {}
    share["atlas"] = 0.3
    share["cms"] = 0.3
    share["gw"] = 0.05
    share["juno"] = 0.05
    share["belle2"] = 0.1
    share["alice"] = 0.1
    share["lhcb"] = 0.1
    totalshare = 0

    atlas = False
    cms = False
    

    for item in explist:
        for item2 in WL_list:
            if item in item2:
                if "atlas" in item and not atlas:
                    expnum += 1
                    totalshare += share[item]
                    atlas = True

                elif "cms" in item and not cms:
                    expnum += 1
                    totalshare += share[item]
                    cms = True
        
                elif "atlas" not in item and "cms" not in item:
                    expnum += 1
                    totalshare += share[item]

    for item in WL_list:
        if "atlas" in item:
            atlasnum += 1

        if "cms" in item:
            cmsnum += 1

    for item in WL_list:
        weights["nom"][item] = 1

        if "atlas" in item:
            weights["exp"][item] = 1 / (float(expnum) * atlasnum)
            weights["grid"][item] = share["atlas"] / (totalshare * atlasnum)

        elif "cms" in item:
            weights["exp"][item] = 1 / (float(expnum) * cmsnum)
            weights["grid"][item] = share["cms"] / (totalshare * cmsnum)

        else:
            weights["exp"][item] = 1 / float(expnum)
            weights["grid"][item] = share[item] / totalshare

    return weights


def CalculateScores(xweights, yweights):
    scores_y = {}
    scores_y["nom"] = []
    scores_y["grid"] = []
    scores_y["exp"] = []

    scores_x = {}
    scores_x["nom"] = []
    scores_x["grid"] = []
    scores_x["exp"] = []

    for key in xweights:
        for i in range(len(cpuList)):
            # create array of weighted workload scores
            wArray_x= [0 for i in range(nWorkloads)]
            wArray_y= [0 for i in range(nWorkloads)]
            zeroTest = False
            for j in range(nWorkloads):
                try: 
                    wgt_x = float(xweights[key][titles[j]])
                except KeyError:
                    wgt_x = 0
                    xweights[key][titles[j]] = 0

                try:
                    wgt_y = float(yweights[key][titles[j]])
                except KeyError:
                    wgt_y = 0
                    yweights[key][titles[j]] = 0

                bmk = float(bmkList[i][j] )
                wArray_x[j] =  bmk ** wgt_x
                wArray_y[j] =  bmk ** wgt_y
                if xweights[key][titles[j]]!=0 and bmk==0: zeroTest = True

            #print( wArray, cpuList[i] )
            # skip CPU if any of the required workload scores are zero
            if zeroTest: 
                #print("===> Incomplete set of workloads")
                continue

            # geometric mean
            x,n,sum = 1,0,0
            for j in range(nWorkloads):
                if xweights[key][titles[j]]==0: continue
                x   = x   * wArray_x[j]
                sum = sum + wArray_x[j]
                n  += xweights[key][titles[j]]
            gmean = x**(1/n)
            mean  = sum/n
            #print(key, gmean, cpuList[i])
            #print("GeoMean = ", gmean, " Mean = ", mean, cpuList[i] )
            scores_x[key].append( [cpuList[i], gmean] )

            x,n,sum = 1,0,0
            for j in range(nWorkloads):
                if yweights[key][titles[j]]==0: continue
                x   = x   * wArray_y[j]
                sum = sum + wArray_y[j]
                n  += yweights[key][titles[j]]
            gmean = x**(1/n)
            mean  = sum/n
            #print(key, gmean, cpuList[i])
            #print("GeoMean = ", gmean, " Mean = ", mean, cpuList[i] )
            scores_y[key].append( [cpuList[i], gmean] )

    return(scores_x, scores_y)
    

def MakePlots(scores_x, scores_y, x_n, y_n):
    gStyle.SetOptStat(0)
    gStyle.SetPadBottomMargin(0.2)
    gStyle.SetTitleSize(0.075,"")
    gStyle.SetLegendTextSize(0.04);
    gStyle.SetLegendFillColor(18);

    gStyle.SetPadRightMargin(0.05);
    gStyle.SetPadLeftMargin(0.15);
    gStyle.SetPadBottomMargin(0.2);
    gStyle.SetOptTitle(0);
    gStyle.SetOptFit(0);
    gStyle.SetPadTickX(1);
    gStyle.SetPadTickY(1);
    gStyle.SetTextFont(132);

    graphAMD = {}
    graphAMDHT = {}
    graphIntel = {}
    graphIntelHT = {}
    AMD_x = {}
    AMDHT_x = {}
    Intel_x = {}
    IntelHT_x = {}
    AMD_y = {}
    AMDHT_y = {}
    Intel_y = {}
    IntelHT_y = {}
    canvas = {}
    text = {}
    hist = {}
    legend = {}
    line = {}
    text = {}

    for key in scores_x:
        AMD_x[key] = arr.array('f')
        AMDHT_x[key] = arr.array('f')
        Intel_x[key] = arr.array('f')
        IntelHT_x[key] = arr.array('f')

        AMD_y[key] = arr.array('f')
        AMDHT_y[key] = arr.array('f')
        Intel_y[key] = arr.array('f')
        IntelHT_y[key] = arr.array('f')

        canvas[key] = TCanvas(key, key, 1200, 800)
        canvas[key].Divide(1, 1)
        canvas[key].cd(1)

        FOM = 0

        for i in range(len(scores_x[key])):
            cpu = scores_x[key][i][0]

            if "Intel" in cpu and "HT1" in cpu:
                Intel_y[key].append(scores_y[key][i][1] / scores_x[key][i][1] - 1)
                Intel_x[key].append(scores_x[key][i][1])
                FOM += abs(scores_y[key][i][1] / scores_x[key][i][1] - 1)
            if "Intel" in cpu and "HT2" in cpu:
                IntelHT_y[key].append(scores_y[key][i][1] / scores_x[key][i][1] - 1)
                IntelHT_x[key].append(scores_x[key][i][1])
                FOM += abs(scores_y[key][i][1] / scores_x[key][i][1] - 1)
            if "AMD" in cpu and "HT1" in cpu:
                AMD_y[key].append(scores_y[key][i][1] / scores_x[key][i][1] - 1)
                AMD_x[key].append(scores_x[key][i][1])
                FOM += abs(scores_y[key][i][1] / scores_x[key][i][1] - 1)
            if "AMD" in cpu and "HT2" in cpu:
                AMDHT_y[key].append(scores_y[key][i][1] / scores_x[key][i][1] - 1)
                AMDHT_x[key].append(scores_x[key][i][1])
                FOM += abs(scores_y[key][i][1] / scores_x[key][i][1] - 1)

        FOM /= len(scores_x[key])
        #print(key, FOM)

        hist[key] = TH2F(key + "hist", "", 20, 0, 2, 50, -0.5, 0.5)
        hist[key].GetYaxis().SetLabelSize( 0.03 )
        title = "HEPscore_{" + str(y_n) + "} / HEPScore_{" + str(x_n) + "} - 1"
        hist[key].GetYaxis().SetTitle(title)
        hist[key].GetYaxis().SetTitleSize( 0.05 )
        hist[key].GetYaxis().SetTitleOffset( 0.6 )

        hist[key].GetXaxis().SetLabelSize( 0.04 )
        hist[key].GetXaxis().SetTitle( "HEPscore_{" + str(x_n) + "}" )
        hist[key].GetXaxis().SetTitleSize( 0.05 )
        hist[key].GetXaxis().SetTitleOffset( 0.8 )
        hist[key].Draw()
     
        graphIntel[key] = TGraph(len(Intel_x[key]), Intel_x[key], Intel_y[key])
        graphIntel[key].SetMarkerStyle(22)
        graphIntel[key].SetMarkerSize(2.0)
        graphIntel[key].SetMarkerColor(2)
        graphIntel[key].Draw("P same")

        graphIntelHT[key] = TGraph(len(IntelHT_x[key]), IntelHT_x[key], IntelHT_y[key])
        graphIntelHT[key].SetMarkerStyle(22)
        graphIntelHT[key].SetMarkerSize(2.0)
        graphIntelHT[key].SetMarkerColor(1)
        graphIntelHT[key].Draw("P same")

        graphAMD[key] = TGraph(len(AMD_x[key]), AMD_x[key], AMD_y[key])
        graphAMD[key].SetMarkerStyle(20)
        graphAMD[key].SetMarkerSize(1.5)
        graphAMD[key].SetMarkerColor(2)
        graphAMD[key].Draw("P same")

        graphAMDHT[key] = TGraph(len(AMDHT_x[key]), AMDHT_x[key], AMDHT_y[key])
        graphAMDHT[key].SetMarkerStyle(20)
        graphAMDHT[key].SetMarkerSize(1.5)
        graphAMDHT[key].SetMarkerColor(1)
        graphAMDHT[key].Draw("P same")

        line[key] = TLine(0, 0, 2, 0)
        line[key].Draw()

        gStyle.SetLegendTextSize(0.03)
        legend[key] = TLegend(0.18,0.7,0.32,0.87)
        legend[key].AddEntry(graphAMD[key], "AMD HT Off ",   "p")
        legend[key].AddEntry(graphIntel[key], "Intel HT Off ", "p")
        legend[key].AddEntry(graphAMDHT[key], "AMD HT On ",   "p")
        legend[key].AddEntry(graphIntelHT[key], "Intel HT On ", "p")
        legend[key].Draw()

        text[key] = TPaveText(0.4, 0.02, 0.6, 0.12, "ndc")
        text[key].AddText("FOM = {:.3f}".format(FOM))
        text[key].Draw()

        plotFile = "ExclusionPlot" + str(y_n) + "vs" + str(x_n) + key + ".gif"
        canvas[key].Print(plotFile)

    return 0
    

# Make two sets of plots: first exclude GW and Juno, then exclude also atlas_sim and alice

WLs_cand = ["alice", "atlas_gen", "atlas_sim", "atlas_reco", "belle2",\
          "cms_digi", "cms_gen_sim", "cms_reco", "lhcb" ]
WLs_nom = ["alice", "atlas_gen", "atlas_sim", "atlas_reco", "belle2",\
          "cms_digi", "cms_gen_sim", "cms_reco", "gw", "juno", "lhcb" ]

yweights = CalculateWeights(WLs_cand)

xweights = CalculateWeights(WLs_nom)

scores_x, scores_y = CalculateScores(xweights, yweights)

MakePlots(scores_x, scores_y, len(WLs_nom), len(WLs_cand))

WLs_cand = ["atlas_gen", "atlas_reco", "belle2",\
          "cms_digi", "cms_gen_sim", "cms_reco", "lhcb" ]
WLs_nom = ["alice", "atlas_gen", "atlas_sim", "atlas_reco", "belle2",\
          "cms_digi", "cms_gen_sim", "cms_reco", "lhcb" ]

yweights = CalculateWeights(WLs_cand)

xweights = CalculateWeights(WLs_nom)

scores_x, scores_y = CalculateScores(xweights, yweights)

MakePlots(scores_x, scores_y, len(WLs_nom), len(WLs_cand))

