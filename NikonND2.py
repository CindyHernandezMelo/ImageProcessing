# -*- coding: utf-8 -*-
"""
Created on Fri Jul 19 15:39:47 2019

@author: LENOVO
"""
# In[1]
#------ Paquetes ------#

##Arreglos
import numpy as np

##Directorios
import os

##Graficas
import matplotlib.pylab as plt

##Procesamiento de imagenes (mirar con cual libreria quedarse)
from skimage.morphology import closing, erosion, white_tophat, opening, disk, reconstruction, local_minima, local_maxima, dilation #, closing, , , square,  ,  white_tophat,
from skimage.filters import gaussian, rank, threshold_otsu, threshold_triangle# threshold_local,sobel,  threshold_sauvola, threshold_niblack
from skimage.color import label2rgb
from skimage import exposure
import cv2

#ND2
from pims import ND2_Reader

#Tiempo
import time

#Guardar variables
import pickle

start = time.time()

# In[2]
#------------Funciones-------------------

def graficar(im1, im2, directorio, nombre):

    a,b = 1,2

    fig, axes = plt.subplots(nrows=a, ncols=b, figsize=(20, 10), sharex=True, sharey=True)
    ax = axes.ravel()

    ax[0].imshow(im1, cmap = 'gray')
    ax[1].imshow(im2, cmap = 'gray')

    for a in ax:
        a.axis('off')

    plt.subplots_adjust(wspace=0, hspace=0,
                        left=0, right=1,
                        bottom=0, top=1)
   
    nomb = os.path.join(directorio, nombre)
    plt.savefig(nomb)
    plt.close()


def binarizar(imagen):
    try:
        VALOR_UMBRAL = threshold_triangle(imagen)
    except:
        VALOR_UMBRAL = imagen[0,0]

    binarizacion = imagen > VALOR_UMBRAL
    return binarizacion

def separar(imag,N_FILAS,N_COLUMNAS,funcion):

    DIM_X, DIM_Y = np.shape(imag)

    sep_x = np.linspace(0,DIM_X,N_FILAS+1   , dtype = 'uint16')
    sep_y = np.linspace(0,DIM_Y,N_COLUMNAS+1, dtype = 'uint16')
    binarizacion = np.zeros([DIM_X,DIM_Y])

    for x in range(0, N_FILAS):
        for y in range(0,N_COLUMNAS):
            i = imag[sep_x[x]:sep_x[x+1], sep_y[y]:sep_y[y+1]]
            binarizacion[sep_x[x]:sep_x[x+1], sep_y[y]:sep_y[y+1]] = funcion(i)

    return binarizacion

def quitar_fondo1(imagen, tiempo):
    clahe = cv2.createCLAHE(clipLimit=20.0, tileGridSize=(8,8))
    imagen = clahe.apply(imagen)
    imagen = opening(imagen, disk(3))
    imagen = exposure. rescale_intensity(imagen,  out_range=(0, 255)).astype('uint8')
    imagen = rank.median(imagen, disk(3))
    
    disco = tiempo *2 + 10
    imagen = white_tophat(imagen,disk(disco))
    return imagen
   
# In[3]
#------------------------------------------------------------------#

directorio = os.getcwd()
path = os.path.join(directorio, '2018-12-05 Biopelícula RpoH Etanol Nikon')
path_prueba = os.path.join(directorio,  'Prueba_NikonND2')

stackcrecimiento = ND2_Reader(os.path.join(path, 'crecimiento' + '.nd2'))
stackcambiomedio = ND2_Reader(os.path.join(path, 'cambio de medio' + '.nd2'))

n_planostomados = 8
planostomados = np.arange(0,n_planostomados)
planoinicio = 14

intensidad = np.zeros([1,n_planostomados])
area = np.zeros([1,n_planostomados])
areaactual = np.zeros([1,n_planostomados])
areamaxima = np.zeros([1,n_planostomados])
mascaraareamax = np.zeros([1024, 1344*n_planostomados], dtype = bool)

tiempo = 0

for i in stackcrecimiento:
    imagenes = np.array(i)
    tiempo = tiempo + 1

    tintensidad = np.zeros([1,n_planostomados])
    tarea = np.zeros([1,n_planostomados])

    for plano in planostomados:
        arreglo_imagen = imagenes[plano + planoinicio ,:,:]
        imagen_reescalada = arreglo_imagen #exposure. rescale_intensity(arreglo_imagen,  out_range=(0, 255)).astype('uint8')
        copia_reescalada = exposure. rescale_intensity(arreglo_imagen,  out_range=(0, 255)).astype('uint8')
             
        imagen_reescalada = quitar_fondo1(imagen_reescalada, tiempo)      
        mascara = binarizar(imagen_reescalada)
        mascara = opening(mascara, disk(3))
       
        areaactual[0,plano] = np.sum(mascara)
       
        if areaactual[0,plano]> areamaxima[0,plano]:
            areamaxima[0,plano] = areaactual[0,plano]
            mascaraareamax[:,1344*plano:1344*(plano+1)] = mascara
        else:
            mascara =  mascaraareamax[:,1344*plano:1344*(plano+1)]
           
        ove1 = label2rgb(mascara, copia_reescalada)
        graficar(arreglo_imagen,ove1, path_prueba, 'crecimientoZ%02d'%(plano + planoinicio) +'T%02d'%(tiempo) + '.tif' )
        print('crecimientoZ%02d'%(plano + planoinicio) +'T%02d'%(tiempo))
        tintensidad[0,plano] = np.mean(arreglo_imagen[mascara])
        tarea[0,plano] = np.sum(mascara)

    intensidad = np.concatenate((intensidad,tintensidad))
    area = np.concatenate((area,tarea))

tiempo = 0

for i in stackcambiomedio:
    imagenes = np.array(i)
    tiempo = tiempo + 1

    tintensidad = np.zeros([1,n_planostomados])
    tarea = np.zeros([1,n_planostomados])

    for plano in planostomados:
        arreglo_imagen = imagenes[plano + planoinicio ,:,:]
        copia_reescalada = exposure. rescale_intensity(arreglo_imagen,  out_range=(0, 255)).astype('uint8') #exposure. rescale_intensity(arreglo_imagen,  out_range=(0, 255)).astype('uint8')
        mascara = mascaraareamax[:,1344*plano:1344*(plano+1)]
       
        ove1 = label2rgb(mascara, copia_reescalada)
        graficar(ove1, arreglo_imagen, path_prueba, 'cambiomedioZ%02d'%(plano + planoinicio) +'T%02d'%(tiempo) + '.tif' )
        print('cambiomedioZ%02d'%(plano + planoinicio) +'T%02d'%(tiempo))
        tintensidad[0,plano] = np.mean(arreglo_imagen[mascara])
        tarea[0,plano] = np.sum(mascara)      

    intensidad = np.concatenate((intensidad,tintensidad))
    area = np.concatenate((area,tarea))

## Saving the objects:
   
infointensidad = os.path.join(path_prueba, 'infointensidad.txt')
infoarea = os.path.join(path_prueba, 'infointensidadarea.txt')

np.savetxt(infointensidad, intensidad)
np.savetxt(infoarea, area)
       
end = time.time()
print(end - start)

