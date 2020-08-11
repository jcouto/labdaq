from .utils import *

def nb_seal_test(task,interval=500,amp=[10,200],**kwargs):
    import pylab as plt
    from matplotlib.animation import FuncAnimation
    plt.matplotlib.style.use('ggplot')
    srate = task.srate    
    if task.mode == 'vc':
        amplitude = amp[0]
    else:
        amplitude = amp[1]
    pulse = np.hstack([np.zeros(int(0.05*srate)),amplitude*np.ones(int(0.05*srate)),np.zeros(int(0.05*srate))])    
    time = np.arange(len(pulse))/srate
    fig = plt.gcf()
    task.load([pulse])
    data = task.run()
    im = plt.plot(time,data,**kwargs)[0]
    
    def animate(change):
        if 'vc' in task.mode :
            amplitude = amp[0]
        else:
            amplitude = amp[1]
        pulse = np.hstack([np.zeros(int(0.05*srate)),amplitude*np.ones(int(0.05*srate)),np.zeros(int(0.05*srate))])    

        task.load([pulse])
        data = task.run()
        dd = np.array(data)
        im.set_ydata(dd)
        Ipre = np.mean(dd[(time<0.03)])
        Istim = np.mean(dd[(time>0.06) & (time<0.09)])
        # This needs an IF because of thje units
        if 'vc' in task.mode :
            R = (amplitude*1e-3/((Istim-Ipre)*1e-12))/1e6   
            plt.title('offset={0:.2f}pA R={1:.3f} MOhm'.format(Ipre,R))
        else:
            R = (amplitude*1e-3/((Istim-Ipre)*1e-12))/1e10   
            plt.title('offset={0:.2f}mV R={1:.3f} MOhm'.format(Ipre,R))
        plt.ylim([np.min(dd),np.max(dd)])
    anim = FuncAnimation(fig, animate, interval=interval)
    return dict(fig = plt.gcf(),ax=plt.gca(),im= im,anim = anim)
