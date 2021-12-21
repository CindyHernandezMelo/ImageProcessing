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
from PIL import Image, ImageSequence
from skimage.morphology import opening, disk, reconstruction, local_minima #, closing, , , square,  ,  white_tophat,
from skimage.filters import  rank, threshold_triangle, threshold_otsu, sobel# threshold_local,sobel,  threshold_sauvola, threshold_niblack
from skimage.color import label2rgb
from skimage import exposure

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

    fig, axes = plt.subplots(nrows=a, ncols=b, figsize=(4, 8), sharex=True, sharey=True)
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
    semilla = np.copy(imagen)* local_minima(imagen, allow_borders = True)
    mascara = imagen
    reconstruccion = reconstruction(semilla, mascara, method='dilation')
    imagen = (imagen - reconstruccion).astype('uint8')
    
    return imagen

# In[3]
#------------------------------------------------------------------#

directorio = os.getcwd()
path_crecimiento = os.path.join(directorio, '2018-11-27_RpoH_Etanol28hsSPIM', 'crecimientoShifted')
path_cambiomedio = os.path.join(directorio, '2018-11-27_RpoH_Etanol28hsSPIM', 'cambiodemedioShifted')
path_prueba = os.path.join(directorio, 'Prueba_SPIM')
nombresCR = [os.path.join(path_crecimiento,file) for file in os.listdir(path_crecimiento) if (file.endswith('.tif') )]
nombresCA = [os.path.join(path_cambiomedio,file) for file in os.listdir(path_cambiomedio) if (file.endswith('.tif') )]
nombresCR= sorted(nombresCR)
nombresCA= sorted(nombresCA)


nombres = nombresCR + nombresCA

areaactual = np.zeros([1,81])
areamaxima = np.zeros([1,81])
mascaraareamax = np.zeros([2560, 960*81], dtype = bool)

intensidad = np.zeros([1,81])
area = np.zeros([1,81])

for nombre in nombres:
    stack = Image.open(nombre)
    frnm = 0
    tintensidad = np.zeros([1,81])
    tarea = np.zeros([1,81])
    
    for frame in ImageSequence.Iterator(stack):
        if frnm > 10 and frnm < 21:
            
            arreglo_imagen = np.array(frame)
            imagen_reescalada = exposure.rescale_intensity(arreglo_imagen,  out_range=(0, 255)).astype('uint8')
            copia__reescalada = imagen_reescalada.copy()
            
            if path_crecimiento in nombre:
                               
                DIAMETRO_DISCO = 3
                imagen_reescalada = rank.median(imagen_reescalada, disk(DIAMETRO_DISCO))
                imagen_reescalada = quitar_fondo(imagen_reescalada)
                mascara = binarizar(imagen_reescalada, threshold_triangle)
                
                mascara = opening(mascara, disk(DIAMETRO_DISCO))
                areaactual[0,frnm] = np.sum(mascara)
                imagen = 'crecimiento' + nombre[86:-4]
                
                if areaactual[0,frnm] > areamaxima[0,frnm]:
                    areamaxima[0,frnm] = areaactual[0,frnm]
                    mascaraareamax[:,960*frnm:960*(frnm+1)] = mascara
                else:
                    mascara = mascaraareamax[:,960*frnm:960*(frnm+1)] 
                    
            else:
                mascara = mascaraareamax[:,960*frnm:960*(frnm+1)] 
                imagen = 'cambiomedio' + nombre[88:-4]
                
            ove1 = label2rgb(mascara, copia__reescalada)
            
            tintensidad[0,frnm] = np.mean(arreglo_imagen[mascara])
            tarea[0,frnm] = np.sum(mascara)
        
            print('Z%02d' %(frnm) + nombre )
            graficar(ove1, arreglo_imagen, path_prueba,  imagen +'Z%02d' %(frnm) +  '.tif')
        
        frnm = frnm + 1
        
    intensidad = np.concatenate((intensidad,tintensidad))
    area = np.concatenate((area,tarea))
           
end = time.time()
print(end - start)

infointensidad = os.path.join(path_prueba, 'infointensidad.txt')
infoarea = os.path.join(path_prueba, 'infointensidadarea.txt')

np.savetxt(infointensidad, intensidad)
np.savetxt(infoarea, area)





