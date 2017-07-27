#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  7 18:44:27 2017

@author: abriosi
"""

from sklearn.base import TransformerMixin

import numpy as np
from scipy.stats import multivariate_normal
import matplotlib.pyplot as plt
import matplotlib as mpl
import seaborn

class MDL_GMM(TransformerMixin):
    
    def __init__(self,kmin=1,
                 kmax=25,
                 regularize=0,
                 threshold=1e-4,
                 covoption=0,
                 max_iters=1000,
                 live_2d_plot=False,
                 check_plot=False):
        
        self.kmin=kmin
        self.kmax=kmax
        self.regularize=regularize
        self.th=threshold
        self.covoption=covoption
        self.live_2d_plot=live_2d_plot
        self.max_iters=max_iters
        self.check_plot=check_plot

    def fit(self, X, y=None, verb=False):
        y=np.array(X)
        
        dl=[]
        npoints=y.shape[0]
        dimens=y.shape[1]
        
        if self.covoption==0:
            npars = (dimens + dimens*(dimens+1)/2);
        elif self.covoption==1:
            npars = 2*dimens
        elif self.covoption==2:
            npars = dimens
        elif self.covoption==3:
            npars = dimens 
        else:
           npars = (dimens + dimens*(dimens+1)/2)
        
        nparsover2 = npars / 2
        
        k = self.kmax
        
        indic = np.zeros((k,npoints))
        randindex = np.random.randint(0,npoints,npoints)
        randindex = np.random.choice(randindex,k)
        estmu = y[randindex]
        
        estpp = (1/k)*np.ones((1,k))
        globcov = np.cov(y,rowvar=False)
        
        estcov=np.empty(globcov.shape+(self.kmax,))
        for i in range(k):
            estcov[:,:,i]=np.diag((np.diag(np.ones((dimens,dimens))*np.max(np.diag(globcov/10)))))
        
        if self.check_plot== True:
            ax = plt.subplot(111)
            plt.title('Random Gaussian Initialization')
            plt.scatter(y[:,0],y[:,1],alpha=0.2,s=10)
            def draw_elipse(ax,estcov,estmu):
                v, w = np.linalg.eigh(estcov)
                u = w[0] / np.linalg.norm(w[0])
                angle = np.arctan2(u[1], u[0])
                angle = 180 * angle / np.pi  # convert to degrees
                v = 2. * np.sqrt(2.) * np.sqrt(v)
                
                ell = mpl.patches.Ellipse(estmu, v[0], v[1],
                                          180 + angle,facecolor='none')
                ell.set_clip_box(ax.bbox)
                ell.set_alpha(1)
                ax.add_artist(ell)
            for i in range(k):
                draw_elipse(ax,estcov[:,:,i],estmu[i])
            plt.show()
        
        semi_indic=np.empty((k,y.shape[0]))
        for i in range(k):
            
            min_eig = np.min(np.real(np.linalg.eigvals(estcov[:,:,i])))
            if min_eig < 0:
                estcov[:,:,i] -= 10*min_eig * np.eye(*estcov[:,:,i].shape)
                
            semi_indic[i,:]=multivariate_normal.pdf(y, estmu[i], estcov[:,:,i], allow_singular=False)
            indic[i,:]=semi_indic[i,:]*estpp[:,i]
        
        countf = 0
        loglike=[]
        kappas=[]
        ##### axis pode ter de ser -1
        loglike.append(np.sum(np.log(np.sum(np.finfo(np.float64).tiny+indic,axis=0))))
        dlength = -loglike[countf] + (nparsover2*np.sum(np.log(estpp))) + (nparsover2 + 0.5)*k*np.log(npoints)
        dl.append(dlength)
        kappas.append(k)
        
        transitions1 = []
        transitions2 = []
        
        mindl = dl[countf]
        self.bestmu = estmu
        self.bestcov = estcov
        
        k_cont = True
        
        iteration=0
        
        while k_cont==True:
            
            cont=True
            
            while cont == True or iteration<self.max_iters:
                
                if verb==True:
                    print('k='+str(k)+' minestpp='+str(np.min(estpp)))
                
                comp = 0
                while comp < k:
                    
                    indic = np.zeros((k,npoints))
                    for i in range(k):
                        indic[i,:]=semi_indic[i,:]*estpp[:,i]
                    
                    normindic = np.divide(indic,(np.finfo(np.float64).tiny+np.kron(np.ones((k,1)),np.sum(indic,axis=0))))
                    
                    normalize = 1/np.sum(normindic[comp,:],axis=0)
                    
                    aux=np.multiply(np.kron(normindic[comp,:],np.ones((dimens,1))),y.T)
        
                    
                    estmu[comp,:] = normalize*np.sum(aux,axis=-1)
                    
                    if self.covoption == 0:
                        estcov[:,:,comp]=normalize*aux.dot(y) - estmu[comp,:][:,np.newaxis]*estmu[comp,:][:,np.newaxis].T + self.regularize*np.identity(dimens)
                    else:
                        raise NameError('Not implemented covoption > 0')
                        
                     
                    estpp[:,comp] = np.max(np.sum(normindic[comp,:])-nparsover2,axis=0)/npoints
                    estpp = estpp/np.sum(estpp)
                    
                    killed = 0
                    
                    if estpp[:,comp]<=0:
                        killed=1
                        
                        transitions1.append(countf)
                        
                        estmu = np.delete(estmu, comp, axis=0)
                        estcov = np.delete(estcov, comp, axis=-1)
                        estpp = np.delete(estpp, comp, axis=-1)
                        semi_indic=np.delete(semi_indic, comp, axis=0)
        
                        k=k-1
                    
                    if killed==0:
                        
                        min_eig = np.min(np.real(np.linalg.eigvals(estcov[:,:,comp])))
                        if min_eig < 0:
                            estcov[:,:,comp] -= 10*min_eig * np.eye(*estcov[:,:,comp].shape)
                        
                        semi_indic[comp,:]=multivariate_normal.pdf(y, estmu[comp], estcov[:,:,comp], allow_singular=False)
                        comp+=1
                    
                countf = countf + 1
                
                indic = np.zeros((k,npoints))
                semi_indic = np.empty((k,y.shape[0]))
                
                for i in range(k):
                    
                    min_eig = np.min(np.real(np.linalg.eigvals(estcov[:,:,i])))
                    if min_eig < 0:
                        estcov[:,:,i] -= 10*min_eig * np.eye(*estcov[:,:,i].shape)
                    
                    semi_indic[i,:]=multivariate_normal.pdf(y, estmu[i], estcov[:,:,i], allow_singular=False)
                    indic[i,:]=semi_indic[i,:]*estpp[:,i]
                
                if k != 1:
                    loglike.append(np.sum(np.log(np.finfo(np.float64).tiny+np.sum(indic,axis=0))))
                else:
                    loglike.append(np.sum(np.log(np.finfo(np.float64).tiny+indic)))
                
                dlength = -loglike[countf] + (nparsover2*np.sum(np.log(estpp))) + (nparsover2 + 0.5)*k*np.log(npoints)
                dl.append(dlength)
                kappas.append(k)
                
                deltlike = loglike[countf] - loglike[countf-1]
                
                if verb==True:
                    toprint=np.abs(deltlike/loglike[countf-1])/self.th
                    print('deltaloglike/th ='+str(toprint))
                    
                if np.abs(deltlike/loglike[countf-1]) < self.th :
                    cont=False
                
                if self.live_2d_plot==True:
                    ### FALSE SHIET PLOT
                    ax = plt.subplot(111)
                    plt.scatter(y[:,0],y[:,1],alpha=0.2,s=10)
                    def draw_elipse(ax,estcov,estmu):
                        v, w = np.linalg.eigh(estcov)
                        u = w[0] / np.linalg.norm(w[0])
                        angle = np.arctan2(u[1], u[0])
                        angle = 180 * angle / np.pi  # convert to degrees
                        v = 2. * np.sqrt(2.) * np.sqrt(v)
                        
                        ell = mpl.patches.Ellipse(estmu, v[0], v[1],
                                                  180 + angle,facecolor='none')
                        ell.set_clip_box(ax.bbox)
                        ell.set_alpha(1)
                        ax.add_artist(ell)
                    for i in range(k):
                        draw_elipse(ax,estcov[:,:,i],estmu[i])
                    plt.show()
                    
                iteration+=1
            
            iteration=0
                
            if dl[countf] < mindl:
                self.bestpp = estpp
                self.bestmu = estmu
                self.bestcov = estcov
                self.bestk = k
                mindl = dl[countf]
            
            if k>self.kmin:
                indminp = np.argmin(estpp)
                
                estmu = np.delete(estmu, indminp, axis=0)
                estcov = np.delete(estcov, indminp, axis=-1)
                estpp = np.delete(estpp, indminp, axis=-1)
                
                k=k-1
                
                estpp = estpp/np.sum(estpp)
                
                transitions2.append(countf)
                
                countf=countf+1
                
                indic = np.zeros((k,npoints))
                semi_indic = np.empty((k,y.shape[0]))
                
                for i in range(k):
                    
                    min_eig = np.min(np.real(np.linalg.eigvals(estcov[:,:,i])))
                    if min_eig < 0:
                        estcov[:,:,i] -= 10*min_eig * np.eye(*estcov[:,:,i].shape)
                    
                    semi_indic[i,:]=multivariate_normal.pdf(y, estmu[i], estcov[:,:,i], allow_singular=False)
                    indic[i,:]=semi_indic[i,:]*estpp[:,i]
                
                if k != 1:
                    loglike.append(np.sum(np.log(np.finfo(np.float64).tiny+np.sum(indic,axis=0))))
                else:
                    loglike.append(np.sum(np.log(np.finfo(np.float64).tiny+indic)))
                
                dlength = -loglike[countf] + (nparsover2*np.sum(np.log(estpp))) + (nparsover2 + 0.5)*k*np.log(npoints)
                dl.append(dlength)
                
        #        countf=countf-1
                kappas.append(k)
            else:
                k_cont=False
        
        if self.check_plot==True:
            plt.title('Description Length')        
            plt.plot(range(len(dl)),dl)
            plt.show()
            
            
            plt.title('Best number of components')
            ax = plt.subplot(111)
            plt.scatter(y[:,0],y[:,1],alpha=0.2,s=10)
            def draw_elipse(ax,estcov,estmu):
                v, w = np.linalg.eigh(estcov)
                u = w[0] / np.linalg.norm(w[0])
                angle = np.arctan2(u[1], u[0])
                angle = 180 * angle / np.pi  # convert to degrees
                v = 2. * np.sqrt(2.) * np.sqrt(v)
                
                ell = mpl.patches.Ellipse(estmu, v[0], v[1],
                                          180 + angle,facecolor='none')
                ell.set_clip_box(ax.bbox)
                ell.set_alpha(1)
                ax.add_artist(ell)
            for i in range(self.bestcov.shape[-1]):
                draw_elipse(ax,self.bestcov[:,:,i],self.bestmu[i])
            plt.show()
        return self
    
    def sample(self,sample):
        output=[]
        select_sample=np.random.multinomial(sample, self.bestpp[0])
        gmm=0
        for i in select_sample:
            for i in range(i):
                output.append(np.random.multivariate_normal(self.bestmu[gmm],np.swapaxes(self.bestcov,0,2)[gmm]))
            gmm+=1
        return np.array(output)

    def transform(self, X, y=None):
        y=np.array(X)
        semi_indic = np.empty((self.bestmu.shape[0],y.shape[0]))
        for i in range(self.bestmu.shape[0]):
                    semi_indic[i,:]=multivariate_normal.pdf(y, self.bestmu[i], self.bestcov[:,:,i], allow_singular=False)
        return semi_indic.T
    
    def fit_transform(self, X, y=None):
        self.fit(X)
        return self.transform(X)
    
    def predict_proba(self, X):
        return self.transform(X)
    
    def predict(self, X):
        return np.argmax(self.transform(X),axis=1)
        