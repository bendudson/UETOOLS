class PostProcessors:
    


    def xvert(self, arr):
        from numpy import zeros_like
        """" Returns values of arr on x-vertices (staggered grid)

        index      x-1      x       x+1  
            _________________________
        iy  |  ix-1 |   ix  | ix+1  |
            |_______|_______|_______|
        """
        try:
            self.ixp1
        except:
            self.ixp1 = self.get('ixp1')
        retvar = zeros_like(arr)
        retvar[:-1] = 0.5*(arr[:-1] + arr[1:])
        if self.snull:
            # Account for the X-point cuts
            for ix in [self.ixpt1, self.ixpt2]:
                for iy in range(self.iysptrx+1):
                    retvar[ix, iy] = 0.5*(
                        arr[ix, iy] +  arr[self.ixp1[ix, iy], iy])
        else:
            raise ValueError('dnull xvert not implemented')
        return retvar

    def dxv(self, arr):
        from numpy import zeros
        """ Returns differentiaties arr at the vertices
        """
        return
        try:
            self.ixm1
        except:
            self.ixm1 = self.get('ixm1')
        retvar = zeros_like(arr)
        retvar[:-1] = (arr[1:] + arr[:-1])
        if self.snull:
            # Account for the X-point cuts
            for ix in [self.ixpt1, self.ixpt2]:
                for iy in range(self.iysptrx+1):
                    retvar[ix, iy] = 0.5*(
                        arr[ix, iy] +  arr[self.ixp1[ix, iy], iy])
        else:
            raise ValueError('dnull xvert not implemented')
        return retvar


        return

    def dxc(self, arr):
        from numpy import zeros
        """ Returns differentiaties arr at cell centers
        """
        return


    def yvert(self, arr):
        if self.snull:
            1
        else:
            raise ValueError('dnull yvert not implemented')
        return
    

    def set_psinormc(self, simagxs=None, sibdrys=None):
        if simagxs is None:
            simagxs = self.get('simagxs')
        if sibdrys is None:
            sibdrys = self.get('sibdrys')
        self.psinormc =  (self.get('psi')[self.get('ixmp'),:,0]-simagxs)/ \
            (sibdrys-simagxs)

    def set_psinormf(self, simagxs=None, sibdrys=None):
        if simagxs is None:
            simagxs = self.get('simagxs')
        if sibdrys is None:
            sibdrys = self.get('sibdrys')
        psi = self.get('psi')[self.get('ixmp')]
        self.psinormf = ((0.5*(psi[:,3] + psi[:,4])) -simagxs)/ \
            (sibdrys-simagxs)


    def calc_forcebalance(self, cutlo=1e-300):
        """ Calculates the force-balance terms
        """
        from numpy import minimum, zeros, zeros_like, sum
        from sys import modules
        self.forcebalance = {}

        # Load all variables necessary to the local namespace
        for var in ['ev', 'misotope', 'natomic', 'mi', 'zi', 'rrv', 'gpex', 
            'gpix', 'gtex', 'gtix', 'pri', 'netap', 'qe', 'fqp', 'sx',
            'alfe', 'loglambda', 'betai', 'ex', 'vol', 'up', 'volmsor',
            'pondomfpari_use',
        ]:
            setattr(modules[__name__], var, self.get(var))       


        # Get flux-limit factor
        den = zeros((misotope, self.get('nchstate')) + self.get('ne').shape )
        gradt = zeros((misotope, self.get('nchstate')) + self.get('ne').shape )
        gradp = zeros((misotope, self.get('nchstate')) + self.get('ne').shape )
        upi = zeros(self.get('ne').shape + (sum(natomic),))
        upi_gradp = zeros(self.get('ne').shape + (sum(natomic),))
        upi_alfe = zeros(self.get('ne').shape + (sum(natomic),))
        upi_betai = zeros(self.get('ne').shape + (sum(natomic),))
        upi_ex = zeros(self.get('ne').shape + (sum(natomic),))
        upi_volmsor = zeros(self.get('ne').shape + (sum(natomic),))
        taudeff = zeros(self.get('ne').shape + (sum(natomic),))

        ni = self.get('ni')
        den[0, 0] = self.xvert(self.get('ne'))
        den[1, 0] = self.xvert(ni[:, :, 0])
        tempa = self.xvert(self.get('te'))
        tif = self.xvert(self.get('ti'))

        ltmax = minimum(    abs(tempa/(rrv*gtex + cutlo)),
                            abs(tif/(rrv*gtix + cutlo)),
                            abs(den[0, 0]*tempa/(rrv*gpex + cutlo))
        )
        # Approx Coulomb mfps
        lmfpe = 1e16*( (tempa/ev)**2/(den[0, 0] + cutlo))
        lmfpi = 1e16*( (tif/ev)**2/(den[0, 0] + cutlo))
        # Get ion-pressure gradient scale-lengths
        ltmax = minimum(
                    ltmax, 
                    abs(self.xvert(pri[:,:,0])/(rrv*gpix[:,:,0] + cutlo))
        )
        # Get flux-limit factor
        flxlimf = 1/ (1 + self.get('fricflf') * ((lmfpe + lmfpi)/\
                (ltmax + cutlo))**2)
        gradp[0, 0] = rrv * gpex
        gradt[0, 0] = rrv * gtex
        # Get total impurity density
        # TODO: What happens to misotope and natomic when ishymol>0??
        ionspecies = [natomic[x] for x in range(2, misotope)]
#        dztot = sum(
#            self.xvert(self.get('ni'))[2:2+sum(ionspecies)], 
#            axis=2
#        )
        ifld = 0
        for misa in range(2, misotope):
            for nz in range(natomic[misa]):
                ifld += 1
                ifld += (self.get('ziin')[ifld] < 1e-10)
                den[misa, nz] = self.xvert(ni[:, :, ifld])
                zeffv = self.xvert(self.get('zeff'))
                gradt[misa, nz] = rrv*gtix
                gradp[misa, nz] = rrv*gpix[:,:,ifld] \
                    - pondomfpari_use[:, :, ifld]
                if self.get('is_z0_imp_const') == 0:
                    z0 = den[0, 0] * zeffv / (den[1, 0] +cutlo) - 1
                else:
                    z0 = z0_imp_const
                taud = self.get('cftaud')*5.624e54*mi[0]**0.5*mi[ifld]*\
                    tif**1.5 / (loglambda*den[misa, nz]*zi[ifld]**2*
                    (mi[0]+mi[ifld]) + cutlo)
                taudeff[:,:,ifld] = flxlimf*taud*den[misa, nz]*(1+2.65*z0)*\
                    (1+0.285*z0)/(den[0, 0] * (1+0.24*z0) * \
                    (1+0.93*z0) + cutlo)

                upi_gradp[:,:,ifld] = -gradp[misa, nz]/ (den[misa,nz] + cutlo)
                upi_gradp[:,:,ifld] *= (taudeff[:,:,ifld]/mi[0])
                upi_alfe[:,:,ifld] = alfe[ifld]*gradt[0, 0] 
                upi_alfe[:,:,ifld] *= (taudeff[:,:,ifld]/mi[0])
                upi_betai[:,:,ifld] = betai[ifld]*gradt[misa, nz]
                upi_betai[:,:,ifld] *= (taudeff[:,:,ifld]/mi[0])
                upi_ex[:,:,ifld] = qe*zi[ifld]*rrv*ex
                upi_ex[:,:,ifld] *= (taudeff[:,:,ifld]/mi[0])
                upi_volmsor[:,:,ifld] = volmsor[:, :, ifld] / \
                    (den[misa, nz] * vol + cutlo)
                upi_volmsor[:,:,ifld] *= (taudeff[:,:,ifld]/mi[0])

                upi[:, :, ifld] = up[:, :, 0] + upi_gradp[:,:,ifld] + \
                    upi_alfe[:,:,ifld] + upi_betai[:,:,ifld] + \
                    upi_ex[:,:,ifld] + upi_volmsor[:,:,ifld]

        self.forcebalance['upi'] = upi
        self.forcebalance['up'] = up[:,:,0]
        self.forcebalance['upi_gradp'] = upi_gradp
        self.forcebalance['upi_alfe'] = upi_alfe
        self.forcebalance['upi_betai'] = upi_betai
        self.forcebalance['upi_ex'] = upi_ex
        self.forcebalance['taudeff'] = taudeff
        self.forcebalance['upi_volmsor'] = upi_volmsor
        


        return upi, self.forcebalance
                 
