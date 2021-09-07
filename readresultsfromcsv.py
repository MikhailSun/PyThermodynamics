import pandas as pd
import makecharts as mc
from matplotlib import pyplot as plt
import pickle
from scipy.interpolate import RectBivariateSpline
import numpy as np

df = pd.read_csv('results_thermodynamics.csv',index_col='Name')
print(df)
#['status/sum of residuals', 'Th', 'Ph', 'Ne', 'n_phys', 'n_phys_abs', 'n_corr', 'N_compr', 'N_turb', 'disbalance1',
# 'Gin_physical', 'Gin_corrected', 'Gcompr_out_physical', 'Angle_compr', 'Compr_betta', 'Tin_compr', 'Pin_compr', 'Pi_compr',
# 'Eff_compr', 'Tout_compr', 'Pout_compr', 'Gin_ks', 'Tin_ks', 'Pin_ks', 'Gt', 'qt', 'alfa_ks', 'Gout_ks', 'Eff_ks', 'Tout_ks',
# 'Pout_ks', 'Gz', 'Tz', 'Pz', 'Eff_t', 'At', 'Gn', 'n_priv_turb', 'turb_betta', 'PRturb', 'Gout_t', 'Tout_t', 'Pout_turb', 'P_otb1_from_compr',
# 'P_otb1_to_turb', 'P_otb2_from_compr', 'P_otb2_to_turb', 'G_otb_k']

n=df.loc['n_phys']
class Geeks:
    pass

data=Geeks()

df.loc['Pout_turb'].apply(lambda x: 1000*x)

for name in df.index.to_list()[1:]:

    list_of_params=[float(val) for val in list(reversed(df.loc[name].to_list()[2:-5]))]
    setattr(data,name,list_of_params)

# Fig1=mc.Chart(points_for_plot=[{'x':data.n_phys,'y':[abs(val) for val in data.N_compr],'label':'Nк'},{'x':data.n_phys,'y':data.N_turb,'label':'Nт'},{'x':data.n_phys,'y':data.disbalance1,'label':'Дисбаланс мощности'}],title='Мощность компрессора и турбины',xlabel='n, об/мин',ylabel='N, кВт',dpi=200,figure_size=(7,5))
# Fig2=mc.Chart(points_for_plot=[{'x':data.n_phys,'y':data.Gin_physical,'label':'Gк вх'},{'x':data.n_phys,'y':data.Gin_corrected,'label':'Gк вх прив'},{'x':data.n_phys,'y':data.Gcompr_out_physical,'label':'Gк вых'},{'x':data.n_phys,'y':data.Gout_ks,'label':'Gкс вых'},{'x':data.n_phys,'y':data.Gz,'label':'Gт са'},{'x':data.n_phys,'y':data.Gout_t,'label':'Gт вых'}],title='Расход воздуха',xlabel='n, об/мин',ylabel='G, кг/с',dpi=200,figure_size=(7,5))
# Fig3=mc.Chart(points_for_plot=[{'x':data.n_phys,'y':data.Compr_betta,'label':'Compr_betta'},{'x':data.n_phys,'y':data.turb_betta,'label':'turb_betta'}],title='betta',xlabel='n, об/мин',ylabel='betta',dpi=200,figure_size=(7,5))
# Fig4=mc.Chart(points_for_plot=[{'x':data.n_phys,'y':data.Pi_compr,'label':'Компрессор'},{'x':data.n_phys,'y':data.PRturb,'label':'Турбина'}],title='Степень изменения давления',xlabel='n, об/мин',ylabel='PR',dpi=200,figure_size=(7,5))
# Fig5=mc.Chart(points_for_plot=[{'x':data.n_phys,'y':data.Th,'label':'Th'},{'x':data.n_phys,'y':data.Tout_compr,'label':'Тк вых'},{'x':data.n_phys,'y':data.Tz,'label':'Тт са'},{'x':data.n_phys,'y':data.Tout_t,'label':'Тт вых'}],title='Температура воздуха/газа по тракту',xlabel='n, об/мин',ylabel='Т, К',dpi=200,figure_size=(7,5))
# Fig6=mc.Chart(points_for_plot=[{'x':data.n_phys,'y':data.Ph,'label':'Ph'},{'x':data.n_phys,'y':data.Pout_compr,'label':'Pк вых'},{'x':data.n_phys,'y':data.Pout_ks,'label':'Pкс вых'},{'x':data.n_phys,'y':data.Pout_turb,'label':'Pт вых'}],title='Давление воздуха/газа по тракту',xlabel='n, об/мин',ylabel='P, кПа',dpi=200,figure_size=(7,5))
# Fig7=mc.Chart(points_for_plot=[{'x':data.n_phys,'y':data.Gt}],title='Расход топлива',xlabel='n, об/мин',ylabel='Gt, кг/с',dpi=200,figure_size=(7,5))
# Fig8=mc.Chart(points_for_plot=[{'x':data.n_phys,'y':data.alfa_ks}],title='Коэффициент избытка воздуха в камере сгорания',xlabel='n, об/мин',ylabel='альфа',dpi=200,figure_size=(7,5))
# Fig9=mc.Chart(points_for_plot=[{'x':data.n_phys,'y':data.At}],title='Пропускная способность турбины',xlabel='n, об/мин',ylabel='А, кг/с*К^0.5/(кгс/см^2)',dpi=200,figure_size=(7,5))
# Fig10=mc.Chart(points_for_plot=[{'x':data.n_phys,'y':data.Eff_ks,'label':'кпд кс'},{'x':data.n_phys,'y':data.Eff_compr,'label':'кпд к'},{'x':data.n_phys,'y':data.Eff_t,'label':'кпд т'}],title='КПД',xlabel='n, об/мин',ylabel='кпд',dpi=200,figure_size=(7,5))


# plt.plot(data.n_phys,data.Tout_compr)
# plt.show()
#КОМПРЕССОР

name_of_file="D://PyThermodynamics//maps//GTE-170//2021_07_31_compr_var2//GTE170_AC_CFD_2021_07_A-30.dat"


with open(name_of_file, 'rb') as f:
   data_new = pickle.load(f)
n_mainrezult,betta_mainrezult,G_mainrezult,PR_mainrezult,Eff_mainrezult=data_new

n_min=0.62
n_max=1.067
betta_min=0
betta_max=1
Eff_Func4=RectBivariateSpline(n_mainrezult,betta_mainrezult, Eff_mainrezult, bbox=[n_min, n_max, betta_min, betta_max], kx=3, ky=3, s=0.001)
G_Func4=RectBivariateSpline(n_mainrezult,betta_mainrezult, G_mainrezult, bbox=[n_min, n_max, betta_min, betta_max], kx=3, ky=3, s=0.001)
PR_Func4=RectBivariateSpline(n_mainrezult,betta_mainrezult, PR_mainrezult,bbox=[n_min, n_max, betta_min, betta_max], kx=3, ky=3, s=0.001)

color_map = plt.get_cmap('coolwarm')
fig, axes = plt.subplots()
fig.set_size_inches(20, 20)
axes.set_xlabel('G, кг/с', fontsize=15)
axes.set_ylabel('PR', fontsize=15)
axes.set_title('Характеристика компрессора.', fontsize=15)

G_map = G_Func4
PR_map = PR_Func4
Eff_map = Eff_Func4
n_min = G_map.get_knots()[0][0] * 10
_n_min2 = np.ceil(n_min)
n_max = G_map.get_knots()[0][-1] * 10
_n_max2 = np.floor(n_max)
betta_min = -0.2
betta_max = 1.2
n_vector = [n_min / 10] + np.arange(_n_min2 / 10, _n_max2 / 10, 0.01).tolist() + [n_max / 10]
n_vector = [x for x in n_vector]
n_vector_hq = np.linspace(n_min / 10, n_max / 10, num=200)
n_vector_hq = [x for x in n_vector_hq]
betta_vector = np.arange(betta_min, betta_max, 0.1)
betta_vector_hq = np.linspace(betta_min, betta_max, num=200)
n_colors = [color_map(i) for i in np.linspace(0, 1, len(n_vector))]
betta_colors = [color_map(i) for i in np.linspace(0, 1, len(betta_vector))]
for ni_color in zip(n_vector, n_colors):
    ni = ni_color[0]
    ncolor = ni_color[1]
    Gvect = []
    PRvect = []
    # Effvect=[]
    for bettai in betta_vector_hq:
        Gvect.append(float(G_map(ni, bettai) ))
        PRvect.append(float(PR_map(ni, bettai) ))
        # Effvect.append(float(Eff_map(ni,bettai)))
    axes.plot(Gvect, PRvect, color=ncolor, linewidth=1.2, linestyle='dotted')
    rot_of_text = np.degrees(np.arctan2((PRvect[0] - PRvect[30]),(Gvect[0] - Gvect[30])))

    axes.text(Gvect[0] - 0.01, PRvect[0] - 0.1, np.round(ni, 3), fontsize=10,rotation=rot_of_text,rotation_mode='anchor') #
for bettai_color in zip(betta_vector, betta_colors):
    bettai = bettai_color[0]
    bettacolor = bettai_color[1]
    Gvect = []
    PRvect = []
    # Effvect=[]
    for ni in n_vector_hq:
        Gvect.append(float(G_map(ni, bettai) ))
        PRvect.append(float(PR_map(ni, bettai) ))
        # Effvect.append(float(Eff_map(ni,bettai)))
    axes.plot(Gvect, PRvect, color=bettacolor, linewidth=1.2, linestyle='dotted')

    axes.text(Gvect[-1], PRvect[-1] +0.03, np.round(bettai, 3), fontsize=10)
PR_contour = PR_map(n_vector_hq, betta_vector_hq)
G_contour = G_map(n_vector_hq, betta_vector_hq)
Eff_contour = Eff_map(n_vector_hq, betta_vector_hq)
eff_max = np.ceil(max(Eff_map.get_coeffs() ) * 100)
lev_up = np.linspace((eff_max - 3) / 100, eff_max / 100, 7).tolist()
lev_mid = np.linspace((eff_max - 10) / 100, (eff_max - 3) / 100, 8)[0:-1].tolist()
lev_down = np.linspace(0.6, (eff_max - 10) / 100, 10)[0:-1].tolist()
lev = lev_down + lev_mid + lev_up
# lev = lev_mid + lev_up
axes.contourf(G_contour, PR_contour, Eff_contour, levels=lev, cmap='jet')
_axes = axes.contour(G_contour, PR_contour, Eff_contour, levels=lev, colors='black', linewidths=0.5)
axes.clabel(_axes, inline=1, fontsize=8, colors='k')
axes.grid()
X = data.Gin_corrected
Y = [p_out/p_in for p_in,p_out in zip(data.Pin_compr,data.Pout_compr)]
# axes.scatter(X, Y, color='black', s=50, marker='+')
axes.plot(X, Y,color='black', marker='.', linestyle='dashed')
# for rez in rezults:
#     X.append(rez.named_main_devices[name].inlet.G_corr)
#     Y.append(rez.named_main_devices[name].PRtt)

# axes.set_xlim([4, 10])
# axes.set_ylim([3, 20])
plt.show()

#ТУРБИНА

# name_of_file="D://PyThermodynamics//maps//GTE-170//2020_10_12_turb_var1//GTE170_turbine_CFD 2020 09.dat"
# color_map = plt.get_cmap('coolwarm')
#
# with open(name_of_file, 'rb') as f:
#    data_new = pickle.load(f)
# n_mainrezult, betta_mainrezult, G_mainrezult, PR_mainrezult, Eff_mainrezult,A_mainrezult,L_mainrezult=data_new
#
# n_min=min(n_mainrezult)
# n_max=max(n_mainrezult)
# betta_min=min(betta_mainrezult)
# betta_max=max(betta_mainrezult)
# Eff_Func4=RectBivariateSpline(n_mainrezult,betta_mainrezult, Eff_mainrezult, bbox=[n_min, n_max, betta_min, betta_max], kx=3, ky=3, s=0.001)
# G_Func4=RectBivariateSpline(n_mainrezult,betta_mainrezult, G_mainrezult, bbox=[n_min, n_max, betta_min, betta_max], kx=3, ky=3, s=0.001)
# PR_Func4=RectBivariateSpline(n_mainrezult,betta_mainrezult, PR_mainrezult,bbox=[n_min, n_max, betta_min, betta_max], kx=3, ky=3, s=0.001)
# A_Func4 = RectBivariateSpline(n_mainrezult, betta_mainrezult, A_mainrezult, bbox=[n_min, n_max, betta_min, betta_max],
#                               kx=5, ky=5, s=0.0001)
# L_Func4 = RectBivariateSpline(n_mainrezult, betta_mainrezult, L_mainrezult, bbox=[n_min, n_max, betta_min, betta_max],
#                               kx=5, ky=5, s=0.0001)
#
#
# fig, axes = plt.subplots()
# fig.set_size_inches(20, 20)
# axes.set_ylabel('G*Т^0.5/P*n, кг/с*К^0.5/кПа', fontsize=15)
# axes.set_xlabel('PR', fontsize=15)
# axes.set_title('Характеристика турбины',
#                fontsize=15)
#
# Cap_map = G_Func4
# PR_map = PR_Func4
# Eff_map = Eff_Func4
# n_min = Cap_map.get_knots()[0][0] * 10
# _n_min2 = np.ceil(n_min)
# n_max = Cap_map.get_knots()[0][-1] * 10
# _n_max2 = np.floor(n_max)
# betta_min = -0.2
# betta_max = 1.2
# n_vector = [n_min / 10] + np.arange(_n_min2 / 10, _n_max2 / 10, 0.05).tolist() + [n_max / 10]
# n_vector_hq = np.linspace(n_min / 10, n_max / 10, num=200)
# betta_vector = np.arange(betta_min, betta_max, 0.1)
# betta_vector_hq = np.linspace(betta_min, betta_max, num=20)
# n_colors = [color_map(i) for i in np.linspace(0, 1, len(n_vector))]
# betta_colors = [color_map(i) for i in np.linspace(0, 1, len(betta_vector))]
# for ni_color in zip(n_vector, n_colors):
#     ni = ni_color[0]
#     ncolor = ni_color[1]
#     Capvect = []
#     PRvect = []
#     # Effvect=[]
#     for bettai in betta_vector_hq:
#         Capvect.append(float(Cap_map(ni, bettai) * ni))
#         PRvect.append(float(PR_map(ni, bettai)))
#         # Effvect.append(float(Eff_map(ni,bettai)))
#     Capvect = np.array([val for val in Capvect])
#     axes.plot(PRvect,Capvect,  color=ncolor, linewidth=1.2, linestyle='dotted')
#     axes.text(PRvect[-1] + 0.03,Capvect[-1],  np.round(ni, 2), fontsize=10)
# for bettai_color in zip(betta_vector, betta_colors):
#     bettai = bettai_color[0]
#     bettacolor = bettai_color[1]
#     Capvect = []
#     PRvect = []
#     # Effvect=[]
#     for ni in n_vector_hq:
#         Capvect.append(float(Cap_map(ni, bettai) * ni))
#         PRvect.append(float(PR_map(ni, bettai)))
#         # Effvect.append(float(Eff_map(ni,bettai)))
#     Capvect = np.array([val for val in Capvect])
#     axes.plot(PRvect,Capvect,  color=bettacolor, linewidth=1.2, linestyle='dotted')
#     axes.text(PRvect[-1],Capvect[-1],  np.round(bettai, 2), fontsize=10)
# PR_contour = PR_map(n_vector_hq, betta_vector_hq)
# Cap_contour = Cap_map(n_vector_hq, betta_vector_hq) * n_vector_hq[:, np.newaxis]
# Eff_contour = Eff_map(n_vector_hq, betta_vector_hq)
# eff_max = np.ceil(max(Eff_map.get_coeffs()) * 100)
# lev_up = np.linspace((eff_max - 3) / 100, eff_max / 100, 7).tolist()
# lev_mid = np.linspace((eff_max - 10) / 100, (eff_max - 3) / 100, 8)[0:-1].tolist()
# lev_down = np.linspace(0.55, (eff_max - 10) / 100, 10)[0:-1].tolist()
# lev = lev_down + lev_mid + lev_up
# axes.contourf(PR_contour,Cap_contour,  Eff_contour, levels=lev, cmap='jet')
# _axes = axes.contour(PR_contour,Cap_contour,  Eff_contour, levels=lev, colors='black', linewidths=0.5)
# axes.clabel(_axes, inline=1, fontsize=8, colors='k')
# axes.grid()
# X = data.PRturb
# Y = data.Gn
# axes.text(11.1,0.026,  'n прив',rotation=-45, fontsize=10)
# axes.plot(X, Y,color='black', linestyle='dashed')
# # axes.set_xlim([4, 10])
# axes.set_ylim([0.012, 0.028])

# for rez in rezults:
#     X.append(rez.named_main_devices[name].throttle.capacity * rez.named_main_devices[name].n_corr)
#     Y.append(rez.named_main_devices[name].PRtt)
#     axes.scatter(X, Y, color='black', s=50, marker='+')
