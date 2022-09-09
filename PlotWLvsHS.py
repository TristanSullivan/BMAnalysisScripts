"""
This function generates plots of the workloads vs. HEPScore
At the moment, HEPScore is the unweighted average of all eleven workloads
To change this, change wMap just below the imports
"""

import array as arr
import ROOT
from ROOT import TCanvas, TH1F, TH2F, TFile, TF1, TPad, TGraphErrors, TLine, TLegend, TLatex, TGraph, TPaveText
from ROOT import gROOT, gStyle, gPad, gApplication

# All workloads equally weighted
# Order is defined by the files list a few lines down
wMap = [1,1,1,1,1,1,1,1,1,1,1]

# workloads in alphabetical order
dir = "./latestfiles_sep6/"
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
titles = ["Alice", "atlas_gen_sherpa", "atlas_sim_mt", "atlas_reco_mt", "Belle2",\
          "cms_digi", "cms_gen_sim", "cms_reco", "GW", "Juno", "LHCb" ]

# read data and fill array with (cpulabel and norm-workload)
workloadCPU =  [[] for i in range(len(files))]
workloadBmk =  [[] for i in range(len(files))]
for i in range(nWorkloads):
    with open(dir+files[i],'r') as f:
        for line in f:
            if "Intel" in line or "AMD" in line:
                line     = line.strip('\n')
                list = line.split()
                cpuLabel = list[0]+"-"+list[3]+"cores-HT"+list[4]+"-"+list[2]
                workloadCPU[i].append( cpuLabel )
                workloadBmk[i].append( list[10] )

# list of all unique CPU-systems
cpuList = []
for i in range(nWorkloads):
    for j in range(len(workloadCPU[i])):
        if not (workloadCPU[i][j] in cpuList):
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

# calculate HEPScore based on wMap
score = []  # list of [cpuLabel and HEPScore (geo-mean)]
nZero = 0
for i in range(len(cpuList)):

    # create array of weighted workload scores
    wArray= [0 for i in range(nWorkloads)]
    zeroTest = False
    for j in range(nWorkloads):
        #print(i,j,wMap[j], bmkList[i][j] )
        wgt = float(wMap[j])
        bmk = float(bmkList[i][j] )
        wArray[j] = wgt * bmk
        if wMap[j]!=0 and wArray[j]==0: zeroTest = True

    #print( wArray, cpuList[i] )
    # skip CPU if any of the required workload scores are zero
    if zeroTest: 
        #print("===> Incomplete set of workloads")
        nZero += 1
        continue

    # geometric mean
    x,n,sum = 1,0,0
    for j in range(nWorkloads):
        if wMap[j]==0: continue
        x   = x   * wArray[j]
        sum = sum + wArray[j]
        n  += wMap[j]
    gmean = x**(1/n)
    mean  = sum/n
    # print("GeoMean = ", gmean, " Mean = ", mean, cpuList[i] )
    score.append( [cpuList[i], gmean] )


#for i in range(len(score)):
#    print(score[i][0], score[i][1])

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

# Need one of each of these per WL
graphAMD = []
graphIntel = []
graphAMDHT = []
graphIntelHT = []

# These contain WL / HS - 1
AMDarray = []
Intelarray = []
AMDHTarray = []
IntelHTarray = []

# These contain HS
AMDarray_HS = []
Intelarray_HS = []
AMDHTarray_HS = []
IntelHTarray_HS = []

canvas = []
hist = []
legend = []
line = []
text = []

for k in range(nWorkloads):
    AMDarray.append(arr.array('f'))
    Intelarray.append(arr.array('f'))
    AMDHTarray.append(arr.array('f'))
    IntelHTarray.append(arr.array('f'))
    AMDarray_HS.append(arr.array('f'))
    Intelarray_HS.append(arr.array('f'))
    AMDHTarray_HS.append(arr.array('f'))
    IntelHTarray_HS.append(arr.array('f'))

    FOM = 0
    canvas.append(TCanvas("c" + str(k), titles[k], 1200, 800))
    canvas[k].Divide(1, 1)
    canvas[k].cd(1)
    for i in range(len(score)):
        for j in range(len(workloadCPU[k])):
            cpu = score[i][0]

            if workloadCPU[k][j] == score[i][0]:
                # Average distance from X axis
                FOM += abs(float(workloadBmk[k][j]) / score[i][1] - 1)

                if "Intel" in cpu and "HT1" in cpu:
                    Intelarray[k].append(float(workloadBmk[k][j]) / score[i][1] - 1)
                    Intelarray_HS[k].append(float(score[i][1]))
                if "Intel" in cpu and "HT2" in cpu:
                    IntelHTarray[k].append(float(workloadBmk[k][j]) / score[i][1] - 1)
                    IntelHTarray_HS[k].append(score[i][1])
                if "AMD" in cpu and "HT1" in cpu:
                    AMDarray[k].append(float(workloadBmk[k][j]) / score[i][1] - 1)
                    AMDarray_HS[k].append(float(score[i][1]))
                if "AMD" in cpu and "HT2" in cpu:
                    AMDHTarray[k].append(float(workloadBmk[k][j]) / score[i][1] - 1)
                    AMDHTarray_HS[k].append(float(score[i][1]))
                #print(workloadCPU[k][j], workloadBmk[k][j], score[i][0], score[i][1])

    FOM /= len(Intelarray[k]) + len(IntelHTarray[k]) + len(AMDarray[k]) + len(AMDHTarray[k])
    print(titles[k], FOM)

    graphAMD.append(TGraph(len(AMDarray[k]), AMDarray_HS[k], AMDarray[k]))
    graphAMDHT.append(TGraph(len(AMDHTarray[k]), AMDHTarray_HS[k], AMDHTarray[k]))
    graphIntel.append(TGraph(len(Intelarray[k]), Intelarray_HS[k], Intelarray[k]))
    graphIntelHT.append(TGraph(len(IntelHTarray[k]), IntelHTarray_HS[k], IntelHTarray[k]))

    # Dummy histogram
    hist.append(TH2F(titles[k] + "hist", "", 20, 0, 2, 50, -0.5, 0.5))
    hist[k].GetYaxis().SetLabelSize( 0.04 )
    hist[k].GetYaxis().SetTitle( titles[k] + "/HEPscore_{11} - 1 ")
    hist[k].GetYaxis().SetTitleSize( 0.04 )
    hist[k].GetYaxis().SetTitleOffset( 1.1 )

    hist[k].GetXaxis().SetLabelSize( 0.04 )
    hist[k].GetXaxis().SetTitle( "HEPscore_{11}" )
    hist[k].GetXaxis().SetTitleSize( 0.04 )
    hist[k].GetXaxis().SetTitleOffset( 1.0 )

    hist[k].Draw()

    graphIntel[k].SetMarkerStyle(22)
    graphIntel[k].SetMarkerSize(2.0)
    graphIntel[k].SetMarkerColor(2)
    graphIntel[k].Draw("Psame")

    graphIntelHT[k].SetMarkerStyle(22)
    graphIntelHT[k].SetMarkerSize(2.0)
    graphIntelHT[k].SetMarkerColor(1)
    graphIntelHT[k].Draw("Psame")

    graphAMD[k].SetMarkerStyle(20)
    graphAMD[k].SetMarkerSize(1.5)
    graphAMD[k].SetMarkerColor(2)
    graphAMD[k].Draw("Psame")

    graphAMDHT[k].SetMarkerStyle(20)
    graphAMDHT[k].SetMarkerSize(1.5)
    graphAMDHT[k].SetMarkerColor(1)
    graphAMDHT[k].Draw("Psame")

    # Line at Y = 0
    line.append(TLine(0, 0, 2, 0))
    line[k].Draw()

    gStyle.SetLegendTextSize(0.03)
    legend.append(TLegend(0.18,0.7,0.32,0.87))
    legend[k].AddEntry(graphAMD[k], "AMD HT Off ",   "p")
    legend[k].AddEntry(graphIntel[k], "Intel HT Off ", "p")
    legend[k].AddEntry(graphAMDHT[k], "AMD HT On ",   "p")
    legend[k].AddEntry(graphIntelHT[k], "Intel HT On ", "p")
    legend[k].Draw()

    # Display FOM
    text.append(TPaveText(0.4, 0.05, 0.5, 0.1, "ndc"))
    text[k].AddText("FOM = {:.3f}".format(FOM))
    text[k].Draw()

    plotFile = "WLvsHS_all/" + titles[k] + ".gif"
    canvas[k].Print(plotFile)

#output = TFile("Graphs.root", "RECREATE")
#for k in range(nWorkloads):
#    graph[k].Write()

#output.Close()

gApplication.Run()

