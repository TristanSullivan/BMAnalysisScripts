# ==================================================================================
# ==================================================================================
import os
import datetime as dt
import array as arr
import ROOT
from ROOT import TCanvas, TH1F, TH2F, TFile, TF1, TPad, TGraphErrors, TLine, TLegend, TLatex, TPaveText
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
#wMap = [1,1,1,0,1,1,1,1,0,0,1]

# Nominal
wMap = [0,1,0,1,1,1,1,1,0,0,1]
# Experiment
#wMap = [0,0.5,0,0.5,1,0.3333,0.3333,0.3333,0,0,1]
# Grid
#wMap = [0,0.2,0,0.2,0.1,0.1333,0.1333,0.1333,0,0,0.1]

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
titles = ["Alice", "atlas_gen", "atlas_sim", "atlas_reco", "Belle2",\
          "cms_digi", "cms_gen_sim", "cms_reco", "GW", "Juno", "LHCb" ]

gTitle = "HEPScore"
for i in range(nWorkloads):
    gTitle += str(wMap[i])
print(gTitle)

#plotFile = gTitle+"_nottop5"+".gif"
plotFile = "ForTFPresentation/HEPScore_Nominal_all" + ".gif"
tableFile = "ForTFPresentation/" + gTitle + "_all" + ".txt"

#print(plotFile)
#print(tableFile)

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
cpuList_top5 = []
cpuList_nottop5 = []
for i in range(nWorkloads):
    for j in range(len(workloadCPU[i])):
        if not (workloadCPU[i][j] in cpuList):
            cpuList.append( workloadCPU[i][j] )

            if "Gold" in workloadCPU[i][j] or "Silver" in workloadCPU[i][j] or ("AMD" in workloadCPU[i][j] and "AMD_EPYC_7551P_32-Core_Processor" not in workloadCPU[i][j]):
                cpuList_top5.append( workloadCPU[i][j] )
                #print("Top 5", workloadCPU[i][j])
            else:
                cpuList_nottop5.append( workloadCPU[i][j] )
                #print("Not top 5", workloadCPU[i][j])
            

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
        wArray[j] =  bmk ** wgt
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
    #print("GeoMean = ", gmean, " Mean = ", mean, cpuList[i] )
    score.append( [cpuList[i], gmean] )

#print()
#print("Ls = ", len(cpuList), len(score), nZero)
#for i in range(len(score)):
#    print( score[i] ) 

#print()
#print("*************************************************************")
#print("HS64")

# =====================================================================
# read in HS06 benchmarks
# =====================================================================
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
            # print(line)
            line     = line.strip('\n')
            lineList = line.split()
            cpuLabel = lineList[0]+"-"+lineList[3]+"cores-HT"+lineList[4]+"-"+lineList[2]
            bmkHS64  = float(lineList[8]) 
            HS64.append( [ cpuLabel, bmkHS64 ] )


#print()
#print(len(HS64))
#for i in range(len(HS64)):
#    print(HS64[i])

# merge HEPScore and HS06 lists
x,y   = arr.array('f'), arr.array('f')
x1,y1 = arr.array('f'), arr.array('f')
x2,y2 = arr.array('f'), arr.array('f')
x3,y3 = arr.array('f'), arr.array('f')
x4,y4 = arr.array('f'), arr.array('f')

FOM = 0
cpu1, cpu2, cpu3, cpu4 = [],[],[],[]
for i in range(len(score)):
    cpu    = score[i][0]
    bScore = score[i][1]

    for j in range(len(HS64)):
        if cpu == HS64[j][0]:
            #print("matching cpu :", cpu )
            bHS = HS64[j][1]
            ratio = bScore/(bHS/bmkRef) - 1
            FOM += abs(ratio)
            if "Intel" in cpu and "HT1" in cpu:
                x1.append(bHS); y1.append(ratio); cpu1.append(cpu)
            if "Intel" in cpu and "HT2" in cpu:
                x2.append(bHS); y2.append(ratio); cpu2.append(cpu)
            if "AMD" in cpu   and "HT1" in cpu:
                x3.append(bHS); y3.append(ratio); cpu3.append(cpu)
            if "AMD" in cpu   and "HT2" in cpu:
                x4.append(bHS); y4.append(ratio); cpu4.append(cpu)

FOM /= (len(cpu1) + len(cpu2) + len(cpu3) + len(cpu4))
print("FOM:", FOM)

n1=len(x1); n2=len(x2); n3=len(x3); n4=len(x4)
z1 = arr.array('f', [0 for i in range(n1) ])
z2 = arr.array('f', [0 for i in range(n2) ])
z3 = arr.array('f', [0 for i in range(n3) ])
z4 = arr.array('f', [0 for i in range(n4) ])

# set up root configuration
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

# stops informational messages
gROOT.ProcessLine( "gErrorIgnoreLevel = 1001;")

# set up canvas
c1 = gROOT.FindObject("c1");
if c1: del c1
c1 = TCanvas("c1", "histograms   ", 10,10,1500,600)

# Top Pad for 2D plot
p11 = gROOT.FindObject("p11")
if p11: del p11
#p11 = TPad( 'p11`', 'pad ', 0.10, 0.50, 0.95, 0.95)
p11 = TPad( 'p11`', 'pad ', 0,0,1,1)
p11.Draw()  # this needs to be here
p11.cd()
gPad.SetGrid()
gPad.SetFrameLineWidth(2)  # set line width around hist-box

# draw a dummy histogram
h1 = gROOT.FindObject("h1")
if h1: del h1
h1 = TH2F("h1","",50,10,50, 50,-0.5,0.5)

h1.GetYaxis().SetLabelSize( 0.04 );
h1.GetYaxis().SetTitle( "HEPscore_{7}/HS06_{64bits}^{norm} - 1 ");
h1.GetYaxis().SetTitleSize( 0.04 );
h1.GetYaxis().SetTitleOffset( 1.1 );

h1.GetXaxis().SetLabelSize( 0.04 );
h1.GetXaxis().SetTitle( "HS06_{64bits} per Physical-Core" );
h1.GetXaxis().SetTitleSize( 0.04 );
h1.GetXaxis().SetTitleOffset( 1.0 );

h1.Draw()

# Intel HT1
ga = gROOT.FindObject("ga");
if ga: del ga
ga = TGraphErrors(n1, x1, y1, z1, z1)
ga.SetMarkerStyle(22)
ga.SetMarkerSize(2.0)
ga.SetMarkerColor(2)
ga.Draw("Psame")

# Intel HT2
gb = gROOT.FindObject("gb");
if gb: del gb
gb = TGraphErrors(n2, x2, y2, z2, z2)
gb.SetMarkerStyle(22)
gb.SetMarkerSize(2.0)
gb.SetMarkerColor(1)
gb.Draw("Psame")

# AMD HT1
gc = gROOT.FindObject("gc");
if gc: del gc
gc = TGraphErrors(n3, x3, y3, z3, z3)
gc.SetMarkerStyle(20)
gc.SetMarkerSize(1.5)
gc.SetMarkerColor(2)
gc.Draw("Psame")

# AMD HT2
gd = gROOT.FindObject("gd");
if gd: del gd
gd = TGraphErrors(n4, x4, y4, z4, z4)
gd.SetMarkerStyle(20)
gd.SetMarkerSize(1.5)
gd.SetMarkerColor(1)
gd.Draw("Psame")

line = TLine(10,0,50,0)
line.Draw()

# legend
gStyle.SetLegendTextSize(0.03)
legend = TLegend(0.18,0.7,0.30,0.87);
legend.AddEntry(gc, "AMD HT Off ",   "p")
legend.AddEntry(ga, "Intel HT Off ", "p")
legend.AddEntry(gd, "AMD HT On ",    "p")
legend.AddEntry(gb, "Intel HT On ",  "p")
legend.Draw()

text = TPaveText(0.4, 0.02, 0.6, 0.12, "ndc")
text.AddText("FOM = {:.3f}".format(FOM))
text.Draw()

# draw canvas and plot file
c1.Draw()
#c1.Print(plotFile)


# write (raw) table to file
# -------------------------

with open(tableFile, 'w') as file:
    file.write('%-50s\n'  % datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S') )
    file.write('%-30s\n' % gTitle)

    file.write('%25s\n' % "Workloads in HEPScore : ")
    for i in range(len(wMap)):
        if wMap[i]>0: file.write('%12s'% titles[i])
    file.write('\n')
    for i in range(len(wMap)):
        if wMap[i]>0: file.write('%12s'% wMap[i])
    file.write('\n')
    file.write('\n')

    file.write('%-80s'   % "CPU")
    file.write('%10s'    % "HS06")
    file.write('%15s'    % "Deviation")
    file.write('\n')

    # AMD HT1
    file.write('\n')
    for i in range(n3):
        file.write('%-80s'  % cpu3[i] )
        file.write('%10.2f' % x3[i] )
        file.write('%15.2f' % y3[i] )
        file.write('\n')

    # Intel HT1
    file.write('\n')
    for i in range(n1):
        file.write('%-80s'  % cpu1[i] )
        file.write('%10.2f' % x1[i] )
        file.write('%15.2f' % y1[i] )
        file.write('\n')
      
    # AMD HT2
    file.write('\n')
    for i in range(n4):
        file.write('%-80s'  % cpu4[i] )
        file.write('%10.2f' % x4[i] )
        file.write('%15.2f' % y4[i] )
        file.write('\n')

    # Intel HT2
    file.write('\n')
    for i in range(n2):
        file.write('%-80s'  % cpu2[i] )
        file.write('%10.2f' % x2[i] )
        file.write('%15.2f' % y2[i] )
        file.write('\n')
    file.write('\n')
    file.write('%-20s'  % "Number of CPU-systems = ")
    file.write('%5d' % len(x1) )
    file.write('%5d' % len(x2) )
    file.write('%5d' % len(x3) )
    file.write('%5d' % len(x4) )
    file.write('\n')
    file.write('%-10s' % "Sum = " )
    file.write('%5s' % str(len(x1)+len(x2)+len(x3)+len(x4)) )
    file.write('\n')

    file.close()

print( plotFile)
print( tableFile )

gApplication.Run()
