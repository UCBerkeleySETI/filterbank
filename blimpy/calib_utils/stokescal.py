from blimpy import Waterfall
import numpy as np
from scipy.optimize import curve_fit
from fluxcal import foldcal

def get_stokes(cross_dat, feedtype='linear'):
    '''Output stokes parameters (I,Q,U,V) for a rawspec
    cross polarization data array'''

    #Compute Stokes Parameters
    if feedtype=='linear':
        #I = XX+YY
        I = cross_dat[:,0,:]+cross_dat[:,1,:]
        #Q = XX-YY
        Q = cross_dat[:,0,:]-cross_dat[:,1,:]
        #U = 2*Re(XY)
        U = 2*cross_dat[:,2,:]
        #V = -2*Im(XY)
        V = -2*cross_dat[:,3,:]

    else if feedtype=='circular':
        #I = LL+RR
        I = cross_dat[:,0,:]+cross_dat[:,1,:]
        #Q = 2*Re(XY)
        Q = 2*cross_dat[:,2,:]
        #U = 2*Im(XY)
        U = -2*cross_dat[:,3,:]
        #V = -2*Im(XY)
        V = cross_dat[:,1,:]-cross_dat[:,0,:]
    else:
        raise ValueError('feedtype must be \'linear\' or \'circular\'')

    #Add middle dimension to match Filterbank format
    I = np.expand_dims(I,axis=1)
    Q = np.expand_dims(Q,axis=1)
    U = np.expand_dims(U,axis=1)
    V = np.expand_dims(V,axis=1)

    #Compute linear polarization
    #L=np.sqrt(np.square(Q)+np.square(U))

    return I,Q,U,V

def convert_to_coarse(data,chan_per_coarse):
    '''
    Converts a data array with length n_chans to an array of length n_coarse_chans
    by averaging over the coarse channels
    '''
    #find number of coarse channels and reshape array
    num_coarse = data.size/chan_per_coarse
    data_shaped = np.array(np.reshape(data,(num_coarse,chan_per_coarse)))

    #Return the average over each coarse channel
    return np.mean(data_shaped[:,2:-1],axis=1)

def phase_offsets(Udat,Vdat,tsamp,chan_per_coarse,fit=False,**kwargs):
    '''
    Calculates phase difference between X and Y feeds given U and V
    data from a noise diode measurement on the target
    '''
    #Fold noise diode data and calculate ON OFF diferences for U and V
    U_OFF,U_ON = foldcal(Udat,tsamp,**kwargs)
    V_OFF,V_ON = foldcal(Vdat,tsamp,**kwargs)
    Udiff = U_ON-U_OFF
    Vdiff = V_ON-V_OFF

    return convert_to_coarse(np.arctan2(Vdiff,Udiff),chan_per_coarse)

def gain_offsets(Idat,Qdat,tsamp,chan_per_coarse,**kwargs):
    '''
    Determines relative gain error in the X and Y feeds for an
    observation given I and Q noise diode data.
    '''
    #Fold noise diode data and calculate ON OFF differences for I and Q
    I_OFF,I_ON = foldcal(Idat,tsamp,**kwargs)
    Q_OFF,Q_ON = foldcal(Qdat,tsamp,**kwargs)

    #Calculate power in each feed for noise diode ON and OFF
    XX_ON = (I_ON+Q_ON)/2
    XX_OFF = (I_OFF+Q_OFF)/2
    YY_ON = (I_ON-Q_ON)/2
    YY_OFF = (I_OFF-Q_OFF)/2

    #Calculate gain offset (divided by 2) as defined in Heiles (2001)
    G = (XX_OFF-YY_OFF)/(XX_OFF+YY_OFF)

    return convert_to_coarse(G,chan_per_coarse)
def apply_Mueller(I,Q,U,V, gain_offsets, phase_offsets, chan_per_coarse):
    '''
    Returns calibrated Stokes parameters for an observation given an array
    of differential gains and phase differences. Use 'hyptrig' to use the Mueller
    matrix in Liao et al. (2018)
    '''

    #Find shape of data arrays and calculate number of coarse channels
    shape = I.shape
    ax0 = I.shape[0]
    ax1 = I.shape[1]
    nchans = I.shape[2]
    ncoarse = nchans/chan_per_coarse

    #Reshape data arrays to separate coarse channels
    I = np.reshape(I,(ax0,ax1,ncoarse,chan_per_coarse))
    Q = np.reshape(Q,(ax0,ax1,ncoarse,chan_per_coarse))
    U = np.reshape(U,(ax0,ax1,ncoarse,chan_per_coarse))
    V = np.reshape(V,(ax0,ax1,ncoarse,chan_per_coarse))

    #Swap axes 2 and 3 to in order for broadcasting to work correctly
    I = np.swapaxes(I,2,3)
    Q = np.swapaxes(Q,2,3)
    U = np.swapaxes(U,2,3)
    V = np.swapaxes(V,2,3)

    #Apply top left corner of electronics chain inverse Mueller matrix
    a = 1/(1-gain_offsets**2)
    Icorr = a*(I-gain_offsets*Q)
    Qcorr = a*(-1*gain_offsets*I+Q)

    #Clear uncalibrated I and Q
    I = None
    Q = None

    #Apply bottom right corner of electronics chain inverse Mueller matrix
    Ucorr = U*np.cos(phase_offsets)+V*np.sin(phase_offsets)
    Vcorr = -1*U*np.sin(phase_offsets)+V*np.cos(phase_offsets)

    #Clear uncalibrated U and V
    U = None
    V = None

    #Reshape arrays to original shape
    Icorr = np.reshape(np.swapaxes(Icorr,2,3),shape)
    Qcorr = np.reshape(np.swapaxes(Qcorr,2,3),shape)
    Ucorr = np.reshape(np.swapaxes(Ucorr,2,3),shape)
    Vcorr = np.reshape(np.swapaxes(Vcorr,2,3),shape)

    #Return corrected data arrays
    return Icorr,Qcorr,Ucorr,Vcorr

def calibrate_pols(cross_pols,diode_cross,obsI=None,onefile=True,feedtype='linear',**kwargs):
    '''
    Write four calibrated Stokes filterbank files for a given observation
    with a calibrator noise diode measurement on the source
    '''
    #Obtain time sample length, frequencies, and noise diode data
    obs = Waterfall(diode_cross,max_load=150)
    cross_dat = obs.data
    tsamp = obs.header['tsamp']

    #Calculate number of coarse channels in the noise diode measurement (usually 8)
    dio_ncoarse = obs.calc_n_coarse_chan()
    dio_nchans = obs.header['nchans']
    dio_chan_per_coarse = dio_nchans/dio_ncoarse
    obs = None
    Idat,Qdat,Udat,Vdat = get_stokes(cross_dat,feedtype)
    cross_dat = None
    #Calculate differential gain and phase from noise diode measurements
    print 'Calculating Mueller Matrix variables'
    gams = gain_offsets(Idat,Qdat,tsamp,dio_chan_per_coarse,**kwargs)
    psis = phase_offsets(Udat,Vdat,tsamp,dio_chan_per_coarse,**kwargs)

    #Clear data arrays to save memory
    Idat = None
    Qdat = None
    Udat = None
    Vdat = None

    #Get corrected Stokes parameters
    print 'Opening '+cross_pols
    cross_obs = Waterfall(cross_pols,max_load=150)
    obs_ncoarse = cross_obs.calc_n_coarse_chan()
    obs_nchans = cross_obs.header['nchans']
    obs_chan_per_coarse = obs_nchans/obs_ncoarse

    print 'Grabbing Stokes parameters'
    I,Q,U,V = get_stokes(cross_obs.data,feedtype)

    print 'Applying Mueller Matrix'
    I,Q,U,V = apply_Mueller(I,Q,U,V,gams,psis,obs_chan_per_coarse)

    #Use onefile (default) to produce one filterbank file containing all Stokes information
    if onefile==True:
        cross_obs.data[:,0,:] = np.squeeze(I)
        cross_obs.data[:,1,:] = np.squeeze(Q)
        cross_obs.data[:,2,:] = np.squeeze(U)
        cross_obs.data[:,3,:] = np.squeeze(V)
        cross_obs.write_to_fil(cross_pols[:-15]+'.SIQUV.polcal.fil')
        print 'Calibrated Stokes parameters written to '+cross_pols[:-15]+'.SIQUV.polcal.fil'
        return

    #Write corrected Stokes parameters to four filterbank files if onefile==False
    obs = Waterfall(obs_I,max_load=150)
    obs.data = I
    obs.write_to_fil(cross_pols[:-15]+'.SI.polcal.fil')   #assuming file is named *.cross_pols.fil
    print 'Calibrated Stokes I written to '+cross_pols[:-15]+'.SI.polcal.fil'

    obs.data = Q
    obs.write_to_fil(cross_pols[:-15]+'.Q.polcal.fil')   #assuming file is named *.cross_pols.fil
    print 'Calibrated Stokes Q written to '+cross_pols[:-15]+'.Q.polcal.fil'

    obs.data = U
    obs.write_to_fil(cross_pols[:-15]+'.U.polcal.fil')   #assuming file is named *.cross_pols.fil
    print 'Calibrated Stokes U written to '+cross_pols[:-15]+'.U.polcal.fil'

    obs.data = V
    obs.write_to_fil(cross_pols[:-15]+'.V.polcal.fil')   #assuming file is named *.cross_pols.fil
    print 'Calibrated Stokes V written to '+cross_pols[:-15]+'.V.polcal.fil'


def fracpols(str, **kwargs):
    '''Output fractional linear and circular polarizations for a
    rawspec cross polarization .fil file'''

    I,Q,U,V,L=get_stokes(str, **kwargs)
    return L/I,V/I

def write_stokefils(str, str_I, Ifil=False, Qfil=False, Ufil=False, Vfil=False, Lfil=False, **kwargs):
    '''Writes up to 5 new filterbank files corresponding to each Stokes
    parameter (and total linear polarization L) for a given cross polarization .fil file'''

    I,Q,U,V,L=get_stokes(str, **kwargs)
    obs = Waterfall(str_I, max_load=150) #Load filterbank file to write stokes data to
    if Ifil:
        obs.data = I
        obs.write_to_fil(str[:-15]+'.I.fil')   #assuming file is named *.cross_pols.fil

    if Qfil:
        obs.data = Q
        obs.write_to_fil(str[:-15]+'.Q.fil')   #assuming file is named *.cross_pols.fil

    if Ufil:
        obs.data = U
        obs.write_to_fil(str[:-15]+'.U.fil')   #assuming file is named *.cross_pols.fil

    if Vfil:
        obs.data = V
        obs.write_to_fil(str[:-15]+'.V.fil')   #assuming file is named *.cross_pols.fil

    if Lfil:
        obs.data = L
        obs.write_to_fil(str[:-15]+'.L.fil')   #assuming file is named *.cross_pols.fil


def write_polfils(str, str_I, **kwargs):
    '''Writes two new filterbank files containing fractional linear and
    circular polarization data'''

    lin,circ=fracpols(str, **kwargs)
    obs = Waterfall(str_I, max_load=150)

    obs.data = lin
    obs.write_to_fil(str[:-15]+'.linpol.fil')   #assuming file is named *.cross_pols.fil

    obs.data = circ
    obs.write_to_fil(str[:-15]+'.circpol.fil')   #assuming file is named *.cross_pols.fil

#end module