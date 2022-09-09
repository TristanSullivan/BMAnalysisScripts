# ==================================================================================
# ==================================================================================
import os
import datetime as dt
import time
import array as arr
import ROOT
from ROOT import TCanvas, TH1F, TH2F, TFile, TF1, TPad, TGraphErrors, TLine, TLegend, TLatex, TGraph, TPaveText
from ROOT import gROOT, gStyle, gPad, gApplication


debug1 = True

# current date and time
from datetime import datetime
import pytz
tz = pytz.timezone('US/Pacific')

# for pyroot in "batch mode"
#ROOT.gROOT.SetBatch(True)

# bit map of workloads
bitmap = [0,0,0,0,1,0,0,0]
# bitmap = [1,1,1,1,1,1,1,1]

# change to a wgt-map (set to CMS digi for moment)
# wMap = [0,0,0,0,0, 1.0,1.0, 0,0,0, 0]
# nomimal 8 workloads
wMap = [1,1,0,1,1,1,1,1,0,0,1]

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

ArchDate = {"Naples": 2017.25, "Rome": 2019.5, "Milan": 2021.0, "Piledriver": 2012.75, "K10": 2010.0, \
            "Broadwell": 2016.0, "Haswell": 2014.5, "NehalemEP": 2009.0, "CascadeLake": 2019.25, \
            "Skylake": 2017.5, "IceLake": 2021.25, "IvyBridgeEP": 2013.5, "SandyBridgeEP": 2012.0, "WestmereEP": 2010.0}

gTitle = "HEPScore"
for i in range(nWorkloads):
    gTitle += str(wMap[i])
print(gTitle)

plotFile = gTitle+".gif"
tableFile = gTitle+".txt"

#print(plotFile)
#print(tableFile)

# read data and fill array with (cpulabel and norm-workload)
workloadCPU =  [[] for i in range(len(files))]
workloadBmk =  [[] for i in range(len(files))]
CPUArch = {}

for i in range(nWorkloads):
    with open(dir+files[i],'r') as f:
        for line in f:
            if "Intel" in line or "AMD" in line:
                line     = line.strip('\n')
                list = line.split()
                cpuLabel = list[0]+"-"+list[3]+"cores-HT"+list[4]+"-"+list[2]
                workloadCPU[i].append( cpuLabel )
                workloadBmk[i].append( list[10] )  
                CPUArch[cpuLabel] = list[1]

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


# print()
#print(" L = ", len(cpuList))
#for i in range(len(cpuList)):
#    print( cpuList[i], bmkList[i] )


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

specFile = "hs06_score_64bit.txt"

cpuSP,coresSP,htSP,siteSP = [],[],[],[]
bmkSP,ebmkSP              = [],[]
bmkSPpC, ebmkSPpC         = [],[]
bmkHScore                 = []


# HS64 Intel(R)_Xeon(R)_CPU_E5-2650_v4_@_2.20GHz CERN 24 1 20.27 0.08 1.0
bmkRef = float(20.27) # 486

HS64 = []
with open(specFile,'r') as f:
    for line in f:
        if "Intel" in line or "AMD" in line:
            #print(line)
            line     = line.strip('\n')
            lineList = line.split()
            cpuLabel = lineList[0]+"-"+lineList[3]+"cores-HT"+lineList[4]+"-"+lineList[2]
            bmkHS64  = float(lineList[8])
            HS64.append( [ cpuLabel, bmkHS64 ] ) 


for i in range(len(score)):
    print(score[i][0], score[i][1])

print("-----------------------B2--------------------")

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

B2graph = TGraph()
graphAMD = []
graphIntel = []
graphAMDHT = []
graphIntelHT = []
AMDarray = []
Intelarray = []
AMDHTarray = []
IntelHTarray = []
AMDarray_date = []
Intelarray_date = []
AMDHTarray_date = []
IntelHTarray_date = []
canvas = []
hist = []
legend = []
line = []

for k in range(nWorkloads):
    AMDarray.append(arr.array('f'))
    Intelarray.append(arr.array('f'))
    AMDHTarray.append(arr.array('f'))
    IntelHTarray.append(arr.array('f'))
    AMDarray_date.append(arr.array('f'))
    Intelarray_date.append(arr.array('f'))
    AMDHTarray_date.append(arr.array('f'))
    IntelHTarray_date.append(arr.array('f'))

    FOM = 0
    pointcounter = 0
    canvas.append(TCanvas("c" + str(k), titles[k], 1200, 800))
    canvas[k].Divide(1, 1)
    canvas[k].cd(1)
    for i in range(len(HS64)):
        for j in range(len(workloadCPU[k])):
            cpu = workloadCPU[k][j]
            bHs = HS64[i][1] / bmkRef

            #print(workloadCPU[4][i], workloadBmk[4][i])
            if HS64[i][0] == cpu:
                if "Intel" in cpu and "HT1" in cpu:
                    Intelarray[k].append(float(workloadBmk[k][j]) / bHs - 1)
                    Intelarray_date[k].append(ArchDate[CPUArch[cpu]])
                if "Intel" in cpu and "HT2" in cpu:
                    IntelHTarray[k].append(float(workloadBmk[k][j]) / bHs - 1)
                    IntelHTarray_date[k].append(ArchDate[CPUArch[cpu]])
                if "AMD" in cpu and "HT1" in cpu:
                    AMDarray[k].append(float(workloadBmk[k][j]) / bHs - 1)
                    AMDarray_date[k].append(ArchDate[CPUArch[cpu]])
                if "AMD" in cpu and "HT2" in cpu:
                    AMDHTarray[k].append(float(workloadBmk[k][j]) / bHs - 1)
                    AMDHTarray_date[k].append(ArchDate[CPUArch[cpu]])
                #print(workloadCPU[k][j], workloadBmk[k][j], score[i][0], score[i][1])
                #graph[k].SetPoint(pointcounter, score[i][1], float(workloadBmk[k][j]) / score[i][1] - 1)
                #pointcounter = pointcounter + 1

    graphAMD.append(TGraph(len(AMDarray[k]), AMDarray_date[k], AMDarray[k]))
    graphAMDHT.append(TGraph(len(AMDHTarray[k]), AMDHTarray_date[k], AMDHTarray[k]))
    graphIntel.append(TGraph(len(Intelarray[k]), Intelarray_date[k], Intelarray[k]))
    graphIntelHT.append(TGraph(len(IntelHTarray[k]), IntelHTarray_date[k], IntelHTarray[k]))

    hist.append(TH2F(titles[k] + "hist", "", 56, 2008, 2022, 50, -0.5, 0.5))
    hist[k].GetYaxis().SetLabelSize( 0.04 )
    hist[k].GetYaxis().SetTitle( titles[k] + "^{norm}/HS06^{norm} - 1 ")
    hist[k].GetYaxis().SetTitleSize( 0.04 )
    hist[k].GetYaxis().SetTitleOffset( 1.1 )

    hist[k].GetXaxis().SetLabelSize( 0.04 )
    hist[k].GetXaxis().SetTitle( "CPU Release Date" )
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

    line.append(TLine(2008, 0, 2022, 0))
    line[k].Draw()

    gStyle.SetLegendTextSize(0.03)
    legend.append(TLegend(0.18,0.7,0.32,0.87))
    legend[k].AddEntry(graphAMD[k], "AMD HT Off ",   "p")
    legend[k].AddEntry(graphIntel[k], "Intel HT Off ", "p")
    legend[k].AddEntry(graphAMDHT[k], "AMD HT On ",   "p")
    legend[k].AddEntry(graphIntelHT[k], "Intel HT On ", "p")
    legend[k].Draw()

    plotFile = "WLvsyear/" + titles[k] + ".gif"
    canvas[k].Print(plotFile)

    #graph[k].GetXaxis().SetTitle("Nominal HEPscore")
    #graph[k].GetYaxis().SetTitle(titles[k])
    #graph[k].SetMarkerStyle(20)
    #graph[k].Draw("AP")
    #print(titles[k], ": ", graph[k].GetCorrelationFactor())

#output = TFile("Graphs.root", "RECREATE")
#for k in range(nWorkloads):
#    graph[k].Write()

#output.Close()

gApplication.Run()

