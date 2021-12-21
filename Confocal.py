# -*- coding: utf-8 -*-

"""
Created on Thu Jun 13 14:50:34 2019
@author: Cindy Hernandez
"""
# In[1]
#------ Paquetes ------#

##Arreglos
import numpy as np

##Directorios
import os

##Graficas
import matplotlib.pylab as plt
import seaborn as sns
##Procesamiento de imagenes (mirar con cual libreria quedarse)
from PIL import Image, ImageSequence
from skimage.morphology import opening, disk, reconstruction, local_minima #, closing, , , square,  ,  white_tophat,
from skimage.filters import  rank, threshold_triangle# threshold_local,sobel,  threshold_sauvola, threshold_niblack
from skimage.color import label2rgb
from skimage import exposure
from skimage.filters.rank import threshold
#Tiempo
import time

#Guardar variables
import pickle

start = time.time()

# In[2]
#------------Funciones-------------------

def graficar(im1, im2, directorio, nombre):


    fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(30,15))
    ax = axes.ravel()

    ax[0].imshow(im1, cmap = 'gray')
    ax[1].imshow(im2, cmap = 'gray')
    sns.set(style="darkgrid", color_codes=True) 

    ax[0].axis('off')
    ax[1].axis('off')
   
    plt.subplots_adjust(wspace=0, hspace=0,
                        left=0, right=1,
                        bottom=0, top=1)
#    
    nomb = os.path.join(directorio, nombre)
    plt.savefig(nomb)
    plt.close()

def binarizar(imagen, tipo_binarizacion):
    try:
        VALOR_UMBRAL = tipo_binarizacion(imagen)
    except:
        VALOR_UMBRAL = imagen[0,0]

    binarizacion = imagen > VALOR_UMBRAL
    return binarizacion

def separar(imag,N_FILAS,N_COLUMNAS,tipo_binarizacion):

    DIM_X, DIM_Y = np.shape(imag)

    sep_x = np.linspace(0,DIM_X,N_FILAS+1   , dtype = 'uint16')
    sep_y = np.linspace(0,DIM_Y,N_COLUMNAS+1, dtype = 'uint16')
    binarizacion = np.zeros([DIM_X,DIM_Y])

    for x in range(0, N_FILAS):
        for y in range(0,N_COLUMNAS):
            i = imag[sep_x[x]:sep_x[x+1], sep_y[y]:sep_y[y+1]]
            binarizacion[sep_x[x]:sep_x[x+1], sep_y[y]:sep_y[y+1]] = binarizar(i, tipo_binarizacion)

    return binarizacion.astype('bool')

def quitar_fondo(imagen):
    semilla = (rank.minimum(imagen, disk(4)))
    mascara = imagen
    reconstruccion = reconstruction(semilla, mascara, method='dilation')
    imagen = (imagen - reconstruccion).astype('uint8')
   
    return imagen

# In[3]
#------------------------------------------------------------------#

directorio = os.getcwd()
path_crecimiento = os.path.join(directorio, '2018-11-28 Confocal 28hs RpoH etanol','crecimiento.oif.files')
path_cambiomedio = os.path.join(directorio, '2018-11-28 Confocal 28hs RpoH etanol','crecimiento_01.oif.files')
path_prueba = os.path.join(directorio, 'Prueba_confocal')

tiempocrecimiento = 36 
tiempocambiomedio = 72 
n_planostomados = 10
planostomados = np.arange(0,n_planostomados)
planoinicio = 20

area  = []
media = []

intensidad = np.zeros([1,n_planostomados])
area = np.zeros([1,n_planostomados])

areamax = np.zeros(n_planostomados)
areaactual = np.zeros(n_planostomados)
mascarasareamax = np.zeros([1024, 1024*n_planostomados], dtype = bool)
for tiempo in range(1, tiempocrecimiento + tiempocambiomedio + 1):
   
    tintensidad = np.zeros([1,n_planostomados])
    tarea = np.zeros([1,n_planostomados])

    for plano in planostomados:
       
        if tiempo <= tiempocrecimiento:
            nombre = os.path.join( path_crecimiento,'s_C001Z%03d'%(plano + planoinicio) +'T%03d'%(tiempo) + '.tif')
            imagen = Image.open(nombre)
            arreglo_imagen = np.array(imagen)
            imagen_reescalada = exposure. rescale_intensity(arreglo_imagen,  out_range=(0, 255)).astype('uint8')
            copia__reescalada = imagen_reescalada.copy()
           
            DIAMETRO_DISCO = 2
            imagen_reescalada = rank.median(imagen_reescalada, disk(DIAMETRO_DISCO))
           
            imagen_reescalada = quitar_fondo(imagen_reescalada)
            mascara = binarizar(imagen_reescalada, threshold_triangle)
            mascara = opening(mascara, disk(1))
            areaactual[plano] = np.sum(mascara)
            if tiempo>10:
                if areaactual[plano]>areamax[plano]:
                    areamax[plano] = areaactual[plano]
                    mascarasareamax[:, 1024*plano:1024*(plano + 1)] = mascara
                mascara = mascarasareamax[:, 1024*plano:1024*(plano + 1)] 
        else:
            nombre = os.path.join( path_cambiomedio,'s_C001Z%03d'%(plano + planoinicio) +'T%03d'%(tiempo - tiempocrecimiento) + '.tif')
            imagen = Image.open(nombre)
            arreglo_imagen = np.array(imagen)
            mascara = mascarasareamax[:, 1024*plano:1024*(plano + 1)] 
       
        tintensidad[0,plano] = np.mean(arreglo_imagen[mascara])
        tarea[0,plano] = np.sum(mascara)
        
        
        
        if tiempo <= tiempocrecimiento:
            nombreguardar = 'crecimiento'+'s_C001Z%03d'%(plano + planoinicio) +'T%03d'%(tiempo) + '.tif'
        else:
            nombreguardar = 'cambiomedio'+'s_C001Z%03d'%(plano + planoinicio) +'T%03d'%(tiempo - tiempocambiomedio) + '.tif'
        
#        graficar(copia__reescalada,label2rgb(mascara,copia__reescalada),path_prueba, nombreguardar)
       
        print('s_C001Z%03d'%(plano + planoinicio) +'T%03d'%(tiempo))
   
    intensidad = np.concatenate((intensidad,tintensidad))
    area = np.concatenate((area,tarea))
   
## Saving the objects:
    
infointensidad = os.path.join(path_prueba, 'infointensidad.txt')
infoarea = os.path.join(path_prueba, 'infointensidadarea.txt')


np.savetxt(infointensidad, intensidad)
np.savetxt(infoarea, area)

end = time.time()
print(end - start) 

## -*- coding: utf-8 -*-
#
#"""
#Created on Thu Jun 13 14:50:34 2019
#@author: Cindy Hernandez
#"""
## In[1]
##------ Paquetes ------#
#
###Arreglos
#import numpy as np
#
###Directorios
#import os
#
###Graficas
#import matplotlib.pylab as plt
#
###Procesamiento de imagenes (mirar con cual libreria quedarse)
#from PIL import Image, ImageSequence
#from skimage.morphology import opening, disk, reconstruction, local_minima #, closing, , , square,  ,  white_tophat,
#from skimage.filters import  rank, threshold_triangle# threshold_local,sobel,  threshold_sauvola, threshold_niblack
#from skimage.color import label2rgb
#from skimage import exposure
#from skimage.filters.rank import threshold
##Tiempo
#import time
#
##Guardar variables
#import pickle
#
#start = time.time()
#
## In[2]
##------------Funciones-------------------
#
#def graficar(im1, im2, directorio, nombre):
#
#    a,b = 1,2
#
#    fig, axes = plt.subplots(nrows=a, ncols=b, figsize=(12, 7), sharex=True, sharey=True)
#    ax = axes.ravel()
#
#    ax[0].imshow(im1, cmap = 'gray')
#    ax[1].imshow(im2, cmap = 'gray')
#
#    for a in ax:
#        a.axis('off')
#
#    plt.subplots_adjust(wspace=0, hspace=0,
#                        left=0, right=1,
#                        bottom=0, top=1)
#    
#    nomb = os.path.join(directorio, nombre)
#    plt.savefig(nomb)
#    plt.close()
#
#
#def binarizar(imagen, tipo_binarizacion):
#    try:
#        VALOR_UMBRAL = tipo_binarizacion(imagen)
#    except:
#        VALOR_UMBRAL = imagen[0,0]
#
#    binarizacion = imagen > VALOR_UMBRAL
#    return binarizacion
#
#def separar(imag,N_FILAS,N_COLUMNAS,tipo_binarizacion):
#
#    DIM_X, DIM_Y = np.shape(imag)
#
#    sep_x = np.linspace(0,DIM_X,N_FILAS+1   , dtype = 'uint16')
#    sep_y = np.linspace(0,DIM_Y,N_COLUMNAS+1, dtype = 'uint16')
#    binarizacion = np.zeros([DIM_X,DIM_Y])
#
#    for x in range(0, N_FILAS):
#        for y in range(0,N_COLUMNAS):
#            i = imag[sep_x[x]:sep_x[x+1], sep_y[y]:sep_y[y+1]]
#            binarizacion[sep_x[x]:sep_x[x+1], sep_y[y]:sep_y[y+1]] = binarizar(i, tipo_binarizacion)
#
#    return binarizacion.astype('bool')
#
#def quitar_fondo(imagen):
#    semilla = (rank.minimum(imagen, disk(4)))
#    mascara = imagen
#    reconstruccion = reconstruction(semilla, mascara, method='dilation')
#    imagen = (imagen - reconstruccion).astype('uint8')
#    
#    return imagen
#
## In[3]
##------------------------------------------------------------------#
#
#directorio = os.getcwd()
#path_muestras = os.path.join(directorio, '2018-11-28 Confocal 28hs RpoH etanol','crecimiento_01.oif.files')
#path_prueba = os.path.join(directorio, 'Prueba_Confocal')
#nombres = [file for file in os.listdir(path_muestras) if (file.endswith('.tif') and 's_C001' in file)]
#
#os.chdir(path_muestras)
#
#
#area  = []
#media = []
#
#frnm = 1
#
#for nombre in nombres:
#    
#    imagen = Image.open(nombre)
#    arreglo_imagen = np.array(imagen)
#    imagen_reescalada = exposure. rescale_intensity(arreglo_imagen,  out_range=(0, 255)).astype('uint8')
#    copia__reescalada = imagen_reescalada.copy()
#    
#    DIAMETRO_DISCO = 2
#    imagen_reescalada = rank.median(imagen_reescalada, disk(DIAMETRO_DISCO))
#    
#    imagen_reescalada = quitar_fondo(imagen_reescalada)
#    mascara = binarizar(imagen_reescalada, threshold_triangle)
#    mascara = opening(mascara, disk(1))
#    ove1 = label2rgb(mascara, copia__reescalada)
#    
#    media.append(np.mean(arreglo_imagen[mascara]))
#    area.append(np.sum(mascara))
#
#    print(frnm)
#
#    frnm = frnm + 1
#    
#    graficar(ove1, arreglo_imagen, path_prueba, nombre)
#    
#end = time.time()
#print(end - start)
#
##
### Saving the objects:
#objs = os.path.join(path_prueba, 'objs.pkl')
#with open(objs, 'wb') as f:  # Python 3: open(..., 'wb')
#    pickle.dump([nombres, area, media], f)
#    f.close()
#
#
#
#
#
