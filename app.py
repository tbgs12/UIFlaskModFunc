from flask import Flask, render_template
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import util

app = Flask(__name__)

playstore = pd.read_csv("data/googleplaystore.csv")

playstore = playstore[playstore['App'].duplicated()==False]

# bagian ini untuk menghapus row 10472 karena nilai data tersebut tidak tersimpan pada kolom yang benar
playstore.drop([10472], inplace=True)

playstore['Category'] = playstore['Category'].astype('category')

playstore['Installs'] = playstore['Installs'].apply(lambda x: x.replace(',',''))
playstore['Installs'] = playstore['Installs'].apply(lambda x: x.replace('+',''))

# Bagian ini untuk merapikan kolom Size, Anda tidak perlu mengubah apapun di bagian ini
playstore['Size'].replace('Varies with device', np.nan, inplace = True ) 
playstore.Size = (playstore.Size.replace(r'[kM]+$', '', regex=True).astype(float) * \
             playstore.Size.str.extract(r'[\d\.]+([kM]+)', expand=False)
            .fillna(1)
            .replace(['k','M'], [10**3, 10**6]).astype(int))
playstore['Size'].fillna(playstore.groupby('Category')['Size'].transform('mean'),inplace = True)

playstore['Price'] = playstore['Price'].apply(lambda x: x.replace('$',''))
playstore['Price'] = playstore['Price'].astype('float')

# Ubah tipe data Reviews, Size, Installs ke dalam tipe data integer
playstore[['Reviews','Size','Installs']] = playstore[['Reviews','Size','Installs']].astype('int64')

# # This function used to render image as specified image_name
# def render_image(plt, image_name):
#     plt.savefig(image_name,bbox_inches="tight") 
#     # bagian ini digunakan untuk mengconvert matplotlib png ke base64 agar dapat ditampilkan ke template html
#     figfile = BytesIO()
#     plt.savefig(figfile, format='png')
#     figfile.seek(0)
#     figdata_png = base64.b64encode(figfile.getvalue())
#     # variabel result akan dimasukkan ke dalam parameter di fungsi render_template() agar dapat ditampilkan di 
#     # halaman html
#     result = str(figdata_png)[2:-1]
#     return result

@app.route("/")
# This fuction for rendering the table
def index():
    df2 = playstore.copy()

    # Statistik
    top_category = pd.crosstab(index=df2['Category'],columns='Jumlah').sort_values(by='Jumlah',ascending=False).reset_index()
    # Dictionary stats digunakan untuk menyimpan beberapa data yang digunakan untuk menampilkan nilai di value box dan tabel
    stats = {
        'most_categories' : top_category.loc[0,'Category'],
        'total': top_category.loc[0,'Jumlah'],
        'rev_table' : playstore.groupby(['Category','App']).sum().sort_values(by='Reviews',ascending=False).reset_index().head(10).iloc[:,:4].reindex(columns=['Category','App','Reviews','Rating']).to_html(classes=['table thead-light table-striped table-bordered table-hover table-sm'])
    }

    ## Bar Plot
    cat_order = df2.groupby('Category').agg({
    'App' : 'count'
        }).rename({'Category':'Total'}, axis=1).sort_values(by='App',ascending=False).head().reset_index()
    X = cat_order['App']
    Y = cat_order['Category']
    my_colors = 'rgbkymc'
    # bagian ini digunakan untuk membuat kanvas/figure
    fig = plt.figure(figsize=(8,3),dpi=300)
    fig.add_subplot()
    # bagian ini digunakan untuk membuat bar plot
    plt.barh(Y,X, color=my_colors)
    # bagian ini digunakan untuk menyimpan plot dalam format image.png


    # # bagian ini digunakan untuk mengconvert matplotlib png ke base64 agar dapat ditampilkan ke template html
    # figfile = BytesIO()
    # plt.savefig(figfile, format='png')
    # figfile.seek(0)
    # figdata_png = base64.b64encode(figfile.getvalue())
    # # variabel result akan dimasukkan ke dalam parameter di fungsi render_template() agar dapat ditampilkan di 
    # # halaman html
    # result = str(figdata_png)[2:-1]

    cat_order_image = util.render_image(plt, 'cat_order.png')
    
    ## Scatter Plot
    X = df2['Reviews'].values # axis x
    Y = df2['Rating'].values # axis y
    area = playstore['Installs'].values/10000000 # ukuran besar/kecilnya lingkaran scatter plot
    fig = plt.figure(figsize=(5,5))
    fig.add_subplot()
    # isi nama method untuk scatter plot, variabel x, dan variabel y
    plt.scatter(x=X,y=Y, s=area, alpha=0.3)
    plt.xlabel('Reviews')
    plt.ylabel('Rating')
    # plt.savefig('rev_rat.png',bbox_inches="tight")

    # figfile = BytesIO()
    # plt.savefig(figfile, format='png')
    # figfile.seek(0)
    # figdata_png = base64.b64encode(figfile.getvalue())
    # result2 = str(figdata_png)[2:-1]
    rev_rat_img = util.render_image(plt,'rev_rat.png')

    ## Histogram Size Distribution
    X=(df2['Size']/1000000).values
    fig = plt.figure(figsize=(5,5))
    fig.add_subplot()
    plt.hist(X,bins=100, density=True,  alpha=0.75)
    plt.xlabel('Size')
    plt.ylabel('Frequency')
    # plt.savefig('hist_size.png',bbox_inches="tight")

    # figfile = BytesIO()
    # plt.savefig(figfile, format='png')
    # figfile.seek(0)
    # figdata_png = base64.b64encode(figfile.getvalue())
    # result3 = str(figdata_png)[2:-1]
    hist_size_img = util.render_image(plt, 'hist_size.png')


    df2['Revenue (in Millions)'] = (df2['Price'] * df2['Installs'] / 1000000).round(2)
    Paid_App = df2[df2['Type'] == 'Paid'].sort_values(by='Revenue (in Millions)',ascending=False)
    Paid_App_Cat = Paid_App.groupby(['Category','Genres']).sum().sort_values(by='Revenue (in Millions)',ascending=False).head().reset_index()
    Paid_App_Cat.drop(['Rating','Reviews','Installs','Price','Size'], axis=1, inplace=True)
    Paid_App_Cat.set_index('Genres')

    X = Paid_App_Cat['Genres']
    Y = Paid_App_Cat['Revenue (in Millions)']
    my_colors = 'rgbkymc'

    fig = plt.figure(figsize=(10,8),dpi=500)


    fig.add_subplot()

    plt.bar(X,Y)


    plt.xlabel('Genres',weight='bold')
    plt.ylabel('Revenue (in Millions)',weight='bold')

    plt.savefig('paid_app_cat_order.png',bbox_inches="tight") 
    # ## Buatlah sebuah plot yang menampilkan insight di dalam data 
    # df2['Revenue'] = df2['Price'] * df2['Installs']
    # Paid_App = df2[df2['Type'] == 'Paid'].sort_values(by='Revenue',ascending=False)
    # Paid_App_Cat = Paid_App.groupby(['Category']).max().sort_values(by='Revenue',ascending=False).head(10).reset_index()
    # ## code here
    # X = Paid_App_Cat['App']
    # Y = Paid_App_Cat['Revenue']
    # my_colors = 'rgbkymc'
    # # bagian ini digunakan untuk membuat kanvas/figure
    # fig = plt.figure(figsize=(15,5),dpi=500)
    # fig.add_subplot()
    # # bagian ini digunakan untuk membuat bar plot
    # plt.barh(X,Y)
    # # bagian ini digunakan untuk menyimpan plot dalam format image.png
    # # plt.savefig('paid_app_cat_order.png',bbox_inches="tight")
    
    # # figfile = BytesIO()
    # # plt.savefig(figfile, format='png')
    # # figfile.seek(0)
    # # figdata_png = base64.b64encode(figfile.getvalue())
    # # result4 = str(figdata_png)[2:-1] 
    top_5_rev_genre = util.render_image(plt, 'top_5_rev_genre.png')
    # Tambahkan hasil result plot pada fungsi render_template()
    return render_template('index.html', stats=stats, result=cat_order_image, result2=rev_rat_img, result3=hist_size_img, result4=top_5_rev_genre)

if __name__ == "__main__": 
    app.run(debug=True)
