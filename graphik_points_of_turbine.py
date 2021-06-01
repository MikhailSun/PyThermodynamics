import makecharts as mc
import matplotlib.pyplot as plt
f=open('rezults.csv')

for line in f:
    if 'Gn' in line:
        Gn=line.split(',')[3:]
        Gn=list(float(x) for x in Gn)
    if 'PRturb' in line:
        PRturb = line.split(',')[3:]
        PRturb = list(float(x) for x in PRturb)
    if 'Tz' in line:
        Tz = line.split(',')[3:]
        Tz = list(float(x) for x in Tz)
    if 'n_priv' in line:
        n_priv = line.split(',')[3:]
        n_priv = list(float(x) for x in n_priv)
    if 'n_phys' in line:
        n_phys = line.split(',')[3:]
        n_phys = list(float(x) for x in n_phys)
    if 'Ne' in line:
        Ne = line.split(',')[3:]
        Ne = list(float(x) for x in Ne)
    if 'Gin_compr_corrected' in line:
        Gin_compr_corrected = line.split(',')[3:]
        Gin = list(float(x) for x in Gin_compr_corrected)
    if 'Pi_compr' in line:
        Pi_compr = line.split(',')[3:]
        PiK = list(float(x) for x in Pi_compr)


Fig=mc.Chart(points_for_scatter=[{'x':PRturb,'y':Gn,'label':'Gn'},],title='Gn=f(PRturb)',xlabel='PRt',ylabel='Gn',dpi=150,figure_size=(5,5))
Fig2=mc.Chart(points_for_scatter=[{'x':PRturb,'y':Tz,'label':'Tz'},],title='Tz=f(PRturb)',xlabel='PRt',ylabel='Tz',dpi=150,figure_size=(5,5))
Fig3=mc.Chart(points_for_scatter=[{'x':n_phys,'y':Ne,'label':'Ne'},],title='Ne=f(n_phys)',xlabel='n_phys',ylabel='Ne',dpi=150,figure_size=(5,5))
Fig3=mc.Chart(points_for_scatter=[{'x':n_phys,'y':n_priv,'label':'n_priv'},],title='n_priv=f(n_phys)',xlabel='n_phys',ylabel='n_priv',dpi=150,figure_size=(5,5))
Fig3=mc.Chart(points_for_scatter=[{'x':n_phys,'y':Tz,'label':'Tz'},],title='Tz=f(n_phys)',xlabel='n_phys',ylabel='Tz',dpi=150,figure_size=(5,5))
Fig3=mc.Chart(points_for_scatter=[{'x':n_phys,'y':PRturb,'label':'PRturb'},],title='PRturb=f(n_phys)',xlabel='n_phys',ylabel='PRturb',dpi=150,figure_size=(5,5))
Fig3=mc.Chart(points_for_scatter=[{'x':n_phys,'y':Gin,'label':'Gin'},],title='Gin=f(n_phys)',xlabel='n_phys',ylabel='Gin',dpi=150,figure_size=(5,5))
Fig3=mc.Chart(points_for_scatter=[{'x':n_phys,'y':PiK,'label':'PiK'},],title='PiK=f(n_phys)',xlabel='n_phys',ylabel='PiK',dpi=150,figure_size=(5,5))

# plt.show()