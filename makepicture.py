from PIL import Image, ImageDraw, ImageFont
import csv


circle_size = 32
dict = {}


def csv_dict_reader(file):
    reader = csv.DictReader(file, delimiter=',')
    for line in reader:
        dict[line["Name"]] = f'{line["Value"]} {line["Dimension"]}'


names = [["G_in",],
         ["Gpr_ok_in","G_ok_in","Pt_in","Tt_in"],
         ["Gpr_ck_in","Pt_ok_out","Tt_ok_out","G_ok_out"],
         ["Tt_ks_out","G_ks_out"],
         ["G_tk_sa","Pt_tk_sa","Tt_tk_sa"],
         ["G_tk_out","Pt_tk_out","Tt_tk_out"],
         ["C_ck_out","Pt_ck_out","Tt_ck_out","G_ck_out"],
         ["G_ts_sa","Pt_ts_sa","Tt_ts_sa"],
         ["Pt_ts_out","Tt_ts_out","G_ts_out"],
         ["G_out","C_out","Pt_out","Tt_out"]]

dev = [["Mh","Ph","Th"],
       ["sigma_in"],
       ["npr_ok","N_ok","PRtt_ok","kpd_ok"],
       ["npr_ck","N_ck","PRtt_ck","kpd_ck"],
       ["Gt","sigma_ks","alfa_ks","kpd_ks","Ce_hp_metric"],
       ["kpd_tk","n_tk","A_tk","N_tk","PRtt_tk"],
       ["kpd_ts","n_ts","Ne_hp_metric","A_ts","N_ts","PRtt_ts"],
       ["sigma_out","momentum"]]

dev_point = [[(-100,-100),
             (3096,1958),
             (4689,2472),
             (6047,2421),
             (6465,1807),
             (6804,2278),
             (7921,2252),
             (8417,2008)]]

points = [[((2052,2329),(2052,2162)),
          ((3969,3053),(3969,2781)),
          ((5807,3107),(5807,2985)),
          ((6463,2886),(6463,2785)),
          ((6607,2888),(6607,2808)),
          ((7043,2917),(7043,2758)),
          ((6408,2270),(6408,2217)),
          ((7767,2776),(7767,2577)),
          ((8183,2848),(8183,2499)),
          ((8719,3132),(8719,2552))]]


def go(model):
    img = Image.open(f"C:\\PyThermodynamics\\model_{model}.png")
    img.load()
    img.save("C:\\PyThermodynamics\\temp.png")
    
    with open("output_results.csv") as f:
        csv_dict_reader(f)

    img2 = Image.open("C:\\PyThermodynamics\\temp.png")
    img2.load()
    draw = ImageDraw.Draw(img2)

    font = ImageFont.truetype("C:\PyThermodynamics\gost-type-a.ttf", size=80)
    
    _cntH = 0
    
    _vOffset = 3900
    _offsetV = 100
    
    _imageWidth = img2.size[0]
    _offsetH = _imageWidth / (len(dev) + 1)
    
    for n, i in enumerate(dev):
        for m, s in enumerate(i):
            # print(f"{m} {s}")
            draw.text([0 + n*_offsetH, _vOffset + m*_offsetV], f"{dev[n][m]} = {dict[dev[n][m]]}", fill=(255,0,0), font=font)
    
        if n != 0:
            draw.line([dev_point[model][n][0], 685 + dev_point[model][n][1], 0 + n * _offsetH - 20, _vOffset + 0 * _offsetV - 10], fill=(0,0,0), width=4)
            draw.line([0 + n * _offsetH - 20, _vOffset + 0 * _offsetV - 10, 0 + n * _offsetH - 20, _vOffset + (m + 1) * _offsetV - 20], fill=(30,30,30,200), width=4)
    
        draw.ellipse([dev_point[model][n][0] - circle_size / 2, 685 + dev_point[model][n][1] - circle_size / 2, dev_point[model][n][0] +
                      circle_size / 2, 685 + dev_point[model][n][1] + circle_size / 2], fill=(255, 0, 0), width=8)
    
    _vOffset = 800
    _offsetV = 100
    
    for n, i in enumerate(points[model]):
        _cntV = 0
        _imageWidth = img2.size[0]
        _offsetH = _imageWidth / (len(names) + 1)
    
        _cntH += 1
    
        for j, item in enumerate(names[n]):
            draw.text([0+_offsetH*_cntH,_vOffset+_offsetV*_cntV], f"{item} = {dict[item]}", fill=(0,0,255), font=font)
            _cntV += 1
    
        draw.line([0 + _offsetH * _cntH - 20, _vOffset - 10, 0 + _offsetH * _cntH - 20, _vOffset + _offsetV*_cntV - 20],
                  fill=(30,30,30,200), width=4)
        draw.line([0 + _offsetH * _cntH - 20, _vOffset + _offsetV*_cntV - 20, i[1]], fill=(30,30,30), width=4)
    
        draw.line(i, fill=(0, 0, 255), width=8)
    
        for j in i:
            draw.ellipse([j[0] - circle_size / 2, j[1] - circle_size / 2, j[0] + circle_size / 2, j[1] + circle_size / 2],
                         fill=(0, 0, 255), width=8)
            draw.ellipse([j[0] - circle_size / 2, j[1] - circle_size / 2, j[0] + circle_size / 2, j[1] + circle_size / 2],
                         fill=(0, 0, 255), width=8)
    
    img2.save("parameters_scheme.png")