#!/usr/bin/python
# -*- coding: utf-8 -*-
# This is a fork of the odak library, orginal: https://github.com/kunguz/odak
# This particular fork can be found here: https://github.com/jegudmunds/odak

import sys,matplotlib,scipy
#matplotlib.use('Agg')
import matplotlib.pyplot
import mpl_toolkits.mplot3d.art3d as art3d
import scipy.linalg
from matplotlib.mlab import griddata
from matplotlib import cm
from matplotlib.patches import Circle, PathPatch, Ellipse
from mpl_toolkits.mplot3d import axes3d
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from numpy import *
from numpy.fft import *
from math import radians,tan,pi

__author__  = ('Kaan Akşit')

class raytracing():
    
    '''
    Class for performing simple ray tracing calculuations and visualizations

    See "General Ray tracing procedure" from
    G.H. Spencerand M.V.R.K Murty for the theoratical explanation

    '''

    def __init__(self):
        '''
        '''
        seterr(divide='ignore', invalid='ignore')
        pass

    def PlotInit(self,plot2d=False):
        '''
        Initializes a plot object, defaults to a 3D plot
        '''
        # Definition to initiate plot.
        self.plt = matplotlib.pyplot
        # New figure created.
        self.fig = self.plt.figure(figsize=(17, 13))

        if plot2d:
            self.ax = self.fig.gca()
        else:
            # 3D projection is enabled.
            self.ax  = self.fig.gca(projection='3d')

        # Enabling the grid in the figure.
        #self.ax.grid(True, color='k', linewidth=2)
        return True

    def SetPlotFontSize(self,family='normal',weight='normal',size='22'):
        '''
        Todo: Fix this 
        '''
        
        # Definition to set the font type, size and weight in plots.
        font = {'family' : family,
                'weight' : weight,
                'size'   : size}
        matplotlib.rc('font', **font)
        # Enables Latex support in the texts.
        matplotlib.rc('text', usetex=True)
        # Set the ticks font propoerties as well to be on the safe side.
        self.ax.xaxis.label.set_fontsize(size)
        self.ax.yaxis.label.set_fontsize(size)
        self.ax.zaxis.label.set_fontsize(size)
        self.ax.xaxis.label.set_family(family)
        self.ax.yaxis.label.set_family(family)
        self.ax.zaxis.label.set_family(family)
        self.ax.xaxis.label.set_fontweight(weight)
        self.ax.yaxis.label.set_fontweight(weight)
        self.ax.zaxis.label.set_fontweight(weight)
        return True

    def findangles(self,Point1,Point2):
        '''
        Function to find angle between two points if there was a
        line intersecting at both of them.
        Vector to hold angles is created.

        '''
        angles   = []
        # Find the distance in between points.
        distance = self.dist(Point1,Point2)
        # X axis rotation is calculated.
        angles.append(degrees(arccos( (Point2[0]-Point1[0])/distance )))
        # Y axis rotation is calculated.
        angles.append(degrees(arccos( (Point2[1]-Point1[1])/distance )))
        # Z axis rotation is calculated.
        angles.append(degrees(arccos( (Point2[2]-Point1[2])/distance )))
        # Angles are returned.

        return angles

    def GenerateBSpline(self, cv, n=100, degree=3, periodic=False):
        # Definition to generate a bspline.
        # Taken from http://stackoverflow.com/questions/34803197/
        # fast-b-spline-algorithm-with-numpy-scipy
        # CV: control points.
        # n: number of samples.
        # degree: curve degree.
        # periodic: True - curve closed, False - curve open.
        n     = n**2
        # If periodic, extend the point array by count+degree+1
        cv    = asarray(cv)
        count = len(cv)
        if periodic:
            factor, fraction = divmod(count+degree+1, count)
            cv = np.concatenate((cv,) * factor + (cv[:fraction],))
            count = len(cv)
            degree = np.clip(degree,1,degree)
        # If opened, prevent degree from exceeding count-1
        else:
            degree = np.clip(degree,1,count-1)
        # Calculate knot vector
        kv = None
        if periodic:
           kv = np.arange(0-degree,count+degree+degree-1,dtype='int')
        else:
           kv = np.array([0]*degree + range(count-degree+1) + \
                         [count-degree]*degree,dtype='int')

        # Calculate query range
        u = np.linspace(periodic,(count-degree),n)
        # Calculate result
        arange = np.arange(len(u))
        points = np.zeros((len(u),cv.shape[1]))
        for i in xrange(cv.shape[1]):
            points[arange,i] = si.splev(u, (kv,cv[:,i],degree))

        return points

    def dist(self,Point1,Point2):
        # Function to find the distance between two points if there
        # was a line intersecting at both of them.

        return sqrt(sum((array(Point1)-array(Point2))**2))

    def create_vec_euler(self,(x0,y0,z0),(alpha,beta,gamma)):
        # Create a vector which consists of a point and direction, not length

        point = array([[x0],[y0],[z0]])
        alpha = cos(radians(alpha))
        beta  = cos(radians(beta))
        gamma = cos(radians(gamma))
        # Cosines vector.
        cosin = array([[alpha],[beta],[gamma]])

        return array([point.reshape(3,1),cosin.reshape(3,1)])

    def create_vec(self,(x0,y0,z0),(x1,y1,z1)):
        '''
        Create a vector from two given points.

        Returns
        -------

        vec_array : A numpy array representing the vector
        pdist : The distance between the two points

        '''
        
        point = array([[x0],[y0],[z0]])
        # Distance between two points.
        pdist = sqrt( pow((x0-x1),2) + pow((y0-y1),2) + pow((z0-z1),2) )

        if pdist != 0:
            alpha = (x1-x0)/pdist
            beta  = (y1-y0)/pdist
            gamma = (z1-z0)/pdist
        elif pdist == 0:
            alpha = float('nan')
            beta  = float('nan')
            gamma = float('nan')

        # Cosines vector
        cosin = array([[alpha],[beta],[gamma]])
        # returns vector and the distance.

        vec_array = array([point,cosin])
        
        return vec_array, pdist

    def vec_intersect(self,vec1,vec2):
        '''
        Method to calculate the intersection of two vectors.
        '''

        A = array([
                   [vec1[1][0][0], vec2[1][0][0] ],
                   [vec1[1][1][0], vec2[1][1][0] ],
                   [vec1[1][2][0], vec2[1][2][0] ]
                  ])
        
        B = array(
                  [vec1[0][0]-vec2[0][0],
                   vec1[0][1]-vec2[0][1],
                   vec1[0][2]-vec2[0][2]
                  ])

        # LU decomposition solution.
        distances = scipy.linalg.solve(A[:][0:2], B[:][0:2])
        # Check if the given solution matches the initial condition
        # at the third equation.

        if int(abs(dot(A[:][2],distances))) != int(abs(B[:][2])):
           distances[0] = 0
           distances[1] = 0

        # Point vector created.
        Point = array([vec1[0][0][0]-distances[0]*vec1[1][0][0],
                       vec1[0][1][0]-distances[0]*vec1[1][1][0],
                       vec1[0][2][0]-distances[0]*vec1[1][2][0]
                      ])

        return Point, distances

    def cross_vectors(self,vec1,vec2):
        # Multiply two vectors and return the resultant vector.
        # Used method described under:
        # Cross-product: http://en.wikipedia.org/wiki/Cross_product
        angle = cross(vec1[1].transpose()[0],vec2[1].transpose()[0])

        return array([vec1[0],[[angle[0]],[angle[1]],[angle[2]]]])

    def angle_btw_vectors(self,vec0,vec1):
        # Finds angle between two vectors
        # Used method described under:
        # http://www.wikihow.com/Find-the-Angle-Between-Two-Vectors
        angle = vec0[1]*vec1[1]
        angle = angle[0]+angle[1]+angle[2]
        s1    = sqrt(vec0[1][0]**2+vec0[1][1]**2+vec0[1][2]**2)
        s2    = sqrt(vec1[1][0]**2+vec1[1][1]**2+vec1[1][2]**2)
        angle = degrees(arccos(angle/(s1*s2)))

        return angle

    def same_side(self,p1,p2,a,b):
        '''
        # Methodology taken from http://www.blackpawn.com/texts/pointinpoly/
        '''
        ba    = subtract(b,a)
        p1a   = subtract(p1,a)
        p2a   = subtract(p2,a)
        cp1   = cross(ba,p1a)
        cp2   = cross(ba,p2a)

        if dot(cp1,cp2) >= 0:
            return True

        return False

    def isitontriangle(self,pointtocheck,point0,point1,point2,error=0.001):
        '''
        Check if the given point is insight the triangle which represented.
        point0, point1 and point2 are the corners of the triangle.
        '''

        pointtocheck = pointtocheck.reshape(3)
        side0        = self.same_side(pointtocheck,point0,point1,point2)
        side1        = self.same_side(pointtocheck,point1,point0,point2)
        side2        = self.same_side(pointtocheck,point2,point0,point1)
        if side0 == True and side1 == True and side2 == True:
            return True

        return False

    def transform(self,input,(alpha,beta,gamma),(x0,y0,z0)):
        '''

        Arguments
        ---------
        alpha; rotation angle (euler) of x axis.
        beta; rotation angle (euler) of y axis.
        gamma; rotation angle (euler) of z axis.
        x0; x coordinate of origin measured in the reference system.
        y0; y coordinate of origin measured in the reference system.
        z0; z coordinate of origin measured in the reference system.

        Return
        ------
        '''
        alpha  = radians(alpha)
        beta   = radians(beta)
        gamma  = radians(gamma)
        R1     = array([[cos(gamma),-sin(gamma),0],[sin(gamma),cos(gamma),0],[0,0,1]])
        R2     = array([[1,0,0],[0,cos(beta),-sin(beta)],[0,sin(beta),cos(beta)]])
        R3     = array([[cos(alpha),0,-sin(alpha)],[0,1,0],[sin(alpha),0,cos(alpha)]])
        R      = dot(dot(R1,R2),R3)

        output = dot(R,input-array([[x0],[y0],[z0]]))

        return output

    def reflect(self,vec,nvec):
        '''
        Reflect a vector on surface defined by some normal vector

        Used method described in G.H. Spencer and M.V.R.K. Murty,
        General Ray-Tracing Procedure", 1961
        '''
        
        mu = 1
        div = pow(nvec[1,0],2)  + pow(nvec[1,1],2) + \
                      pow(nvec[1,2],2)

        a = mu* ( vec[1,0]*nvec[1,0] + vec[1,1]*nvec[1,1] + \
                  vec[1,2]*nvec[1,2]) / div

        outvec = vec.copy()
        outvec[0,0] = nvec[0,0]
        outvec[0,1] = nvec[0,1]
        outvec[0,2] = nvec[0,2]
        outvec[1,0] = vec[1,0] - 2*a*nvec[1,0]
        outvec[1,1] = vec[1,1] - 2*a*nvec[1,1]
        outvec[1,2] = vec[1,2] - 2*a*nvec[1,2]

        return outvec

    def reflect_normal(self,vec0,vec1):
        '''
        Definition to find reflection normal in between two given vectors.
        '''
        
        mu = 1
        nvec = vec1.copy()
        for k in xrange(1,3):
            a0 = arccos(vec0[1,k])
            a1 = arccos(vec1[1,k])
            nvec[1,k] = cos(a1+(pi-(a0+a1))/2.)

        return nvec

    def snell(self,vec,nvec,n1,n2,error=0.01):
        '''
        Method for Snell's law

        Arguments
        ---------

        n1 (float) : refractive index of the medium 1
        n2 (float) : refractive index of the medium 2

        '''
        
        mu = n1/n2
        div = pow(nvec[1,0],2)  + pow(nvec[1,1],2) + \
                pow(nvec[1,2],2)
        a = mu* (vec[1,0]*nvec[1,0] + vec[1,1]*nvec[1,1] \
                     + vec[1,2]*nvec[1,2]) / div
        
        b = (pow(mu,2)-1) / div
        to = -b*0.5/a
        num = 0
        eps = error*2

        # Newton-Raphson method to find the correct root
        while eps > error:
           num   += 1
           oldto  = to
           v      = pow(to,2) + 2*a*to + b
           deltav = 2*(to+a)
           to     = to - v /deltav
           eps    = abs(oldto-to)
           # Iteration notifier
           #print 'Iteration number: %s, Error: %s' % (num,error)
           # Iteration limit
           if num > 5000:
              return vec

        vec_out      = vec.copy()
        vec_out[0,0] = nvec[0,0]
        vec_out[0,1] = nvec[0,1]
        vec_out[0,2] = nvec[0,2]
        vec_out[1,0] = mu*vec[1,0] + to*nvec[1,0]
        vec_out[1,1] = mu*vec[1,1] + to*nvec[1,1]
        vec_out[1,2] = mu*vec[1,2] + to*nvec[1,2]

        return vec_out

    def FuncQuad(self,k,l,m,quad):
        # Definition to return a 3D point position in quadratic
        # surface definition.
        return pow((k-quad[0])/quad[4],2) + pow((l-quad[1])/quad[5],2) + \
            pow((m-quad[2])/quad[6],2) - pow(quad[3],2)

    def sphere(self,k,l,m,sphere):
        # Definition to return a 3D point position in spherical definition.
        return pow(k-sphere[0],2) + pow(l-sphere[1],2) + \
            pow(m-sphere[2],2) - pow(sphere[3],2)

    def norm_sphere(self,x0,y0,z0,sphere):
        # Definition to return normal of a sphere.
        # Derivatives.
        gradx = 2*(x0-sphere[0])/sphere[3]**2
        grady = 2*(y0-sphere[1])/sphere[3]**2
        gradz = 2*(z0-sphere[2])/sphere[3]**2
        # Perpendicular to tangent surface.
        alpha = degrees(arctan(gradx))+90
        beta = degrees(arctan(grady))+90
        gamma = degrees(arctan(gradz))+90

        # Return a normal vector.
        return self.create_vec_euler((x0,y0,z0),(alpha,beta,gamma))

    def norm_quad(self,x0,y0,z0,quad):
        '''
        Function to return normal of a quadratic surface.
        '''

        # Derivatives.
        gradx = 2/quad[4]*(x0-quad[0])/quad[3]**2
        grady = 2/quad[5]*(y0-quad[1])/quad[3]**2
        gradz = 2/quad[6]*(z0-quad[2])/quad[3]**2

        # Perpendicular to tangent surface.
        alpha = degrees(arctan(gradx))+90
        beta = degrees(arctan(grady))+90
        gamma = degrees(arctan(gradz))+90

        # Return a normal vector.
        return self.create_vec_euler((x0,y0,z0),(alpha,beta,gamma))

    def FindInterQuad(self,vector,quad,error=0.00000001,
                      numiter=1000,iternotify='no'):

        # Definition to return intersection of a ray with a quadratic surface.
        return self.find_interc(vector,quad,self.FuncQuad,
                                  self.norm_quad, error=error,
                                  numiter=numiter, iternotify=iternotify)

    def find_sphere_inter(self,vector,sphere,error=0.00000001,numiter=1000,
                       iternotify='no'):
        '''
        Finds the intersection of a ray with a sphere.
        '''
        
        return self.find_interc(
            vector,sphere, self.sphere, self.norm_sphere,error=error,
            numiter=numiter,iternotify=iternotify)    

    def find_interc(self, vec, SurfParam, Func, FuncNorm,
                      error=0.00000001,numiter=1000,iternotify='no'):
        '''
        Method for finding intercept between a vector and a parametric surface

        '''

        number   = 0
        distance = 1
        olddist  = 0
        shift    = 0
        epsilon  = error*2
        k = vec[0,0,0]
        l = vec[0,1,0]
        m = vec[0,2,0]
        FXYZ = Func(k,l,m,SurfParam)

        if abs(FXYZ) < 0.01:
            shift  = 1.5 * SurfParam[3]
            k += shift * vec[1,0]
            l += shift * vec[1,1]
            m += shift * vec[1,2]

        while epsilon > error:
            number   += 1
            oldFXYZ   = FXYZ
            x = distance * vec[1,0] + k
            y = distance * vec[1,1] + l
            z = distance * vec[1,2] + m
            FXYZ = Func(x,y,z,SurfParam)

            # Secant method is calculated, see wikipedia article
            newdist = distance - FXYZ*(distance-olddist)/(FXYZ-oldFXYZ)
            epsilon = abs(newdist-distance)
            olddist = distance
            distance  = newdist

            # Check if the number of iterations are too great
            if number > numiter:
               return 0, 0

        normvec = FuncNorm(x,y,z,SurfParam)

        return distance+shift, normvec

    def findintersurface(self,vec,(point0,point1,point2)):
        '''
        # Method to find intersection point inbetween a surface and a vector
        # See http://geomalgorithms.com/a06-_intersect-2.html
        '''
        
        vec0,s     = self.create_vec(point0,point1)
        vec1,s     = self.create_vec(point1,point2)
        vec2,s     = self.create_vec(point0,point2)
        nvec       = self.cross_vectors(vec0,vec2)
        f             = point0-vec[0].T
        n             = nvec[1].copy()
        distance      = dot(n.T,f.T)/dot(n.T,vec[1])
        nvec[0][0] = vec[0][0]+distance*vec[1][0]
        nvec[0][1] = vec[0][1]+distance*vec[1][1]
        nvec[0][2] = vec[0][2]+distance*vec[1][2]

        return distance[0][0], nvec

    def plot_vector(self,vec,distance,color='k',plot2d=False,lw=2):
        '''
        Method to plot rays
        '''
        
        x = array([vec[0,0,0], distance * vec[1,0] + vec[0,0,0]])
        y = array([vec[0,1,0], distance * vec[1,1] + vec[0,1,0]])
        z = array([vec[0,2,0], distance * vec[1,2] + vec[0,2,0]])
        
        if plot2d:
            self.ax.plot(x,y,color=color,lw=lw)
        else:
            self.ax.plot(x,y,z,color=color,lw=lw)            

        return True

    def plot_point(self,point,color='g*',contour=False,marker=False):
        # Method to plot a single spot.
        self.ax.plot(array([point[0]]),array([point[1]]),array([point[2]]),color)
        # Plotting contour on 3-axes.
        if contour == True:
            self.ax.contour(array([[-1,0,1],
                                   [-1,0,1],
                                   [-1,0,1]
                                   ]),
                            array([[-1,0,1],
                                   [-1,0,1],
                                   [-1,0,1]
                                   ]),
                            array([[2,4,2],
                                   [1,4,5],
                                   [3,3,3]
                                   ]),
                            zdir='z', offset=-100, cmap=cm.coolwarm)

        # Add text near to the point.
        if marker == True:
            label = '(%.1f, %.1f, %.1f)' % (point[0], point[1], point[2])
            self.ax.text(point[0], point[1], point[2], label)

        return True

    def plot_spherical_lens(self,cx=0.,cy=0.,cz=0.,r=10,c='none',alpha=0.3,
                          PlotFlag=True,plot2d=False,sampleno=100):

        '''
        Arguments
        ---------
        cx : Translation of lens in x-direction. Default = 0.
        cy : Translation of lens in y-direction. Default = 0.
        cz : Translation of lens in z-direction. Default = 0.

        Returns
        ---------
        sp_array : Numpy array describing spherical lens geometry


        '''  
    
        # Method to plot a spherical lens.
        v        = linspace(0, pi, sampleno)
        u        = linspace(0,2*pi,sampleno)
        x        = r * outer(cos(u), sin(v)) + cx
        y        = r * outer(sin(u), sin(v)) + cy
        z        = r * outer(ones(size(u)), cos(v)) + cz

        # Plots surface if flag is raised
        if PlotFlag == True:

            if plot2d:
                self.ax.plot(x, y, alpha=alpha, color='black')

            else:

                self.ax.plot_surface(
                    x, y, z, rstride=8, cstride=8, alpha=alpha,
                    color=c, antialiased=True)

        sp_array = array([cx,cy,cz,r])
        
        return sp_array

    def plot_box(self,cx=0,cy=0,cz=0,w=10,c='none',alpha=0.3):

        points = array([[-w, -w, -w],
                        [w, -w, -w ],
                        [w, w, -w],
                        [-w, w, -w],
                        [-w, -w, w],
                        [w, -w, w ],
                        [w, w, w],
                        [-w, w, w]])

        x = points[:,0]+cx
        y = points[:,0]+cy
        z = points[:,0]+cz

        X, Y = meshgrid([-w, w], [-w, w])
        self.ax.plot_surface(X,Y,w, rstride=8, cstride=8, alpha=alpha,
                color=c, antialiased=True)
        self.ax.plot_surface(X,Y,-w, rstride=8, cstride=8, alpha=alpha,
                color=c, antialiased=True)
        self.ax.plot_surface(X,-w,Y, rstride=8, cstride=8, alpha=alpha,
                color=c, antialiased=True)
        self.ax.plot_surface(X,w,Y, rstride=8, cstride=8, alpha=alpha,
                color=c, antialiased=True)
        self.ax.plot_surface(w,X,Y, rstride=8, cstride=8, alpha=alpha,
                color=c, antialiased=True)
        self.ax.plot_surface(-w,X,Y, rstride=8, cstride=8, alpha=alpha,
                color=c, antialiased=True)


    def CalculateParaboloidMesh(self,spher,sampleno=100,angleu=[0,pi],anglev=[0,2*pi]):

        # Definition to calculate triangular meshed form of a spherical sufrace.
        cx = spher[0]; cy = spher[1]; cz = spher[2]; r = spher[3]
        v           = linspace(angleu[0], angleu[1], sampleno)
        u           = linspace(anglev[0],anglev[1],sampleno)
        tris        = zeros((sampleno,sampleno,3))
        tris[:,:,0] = r * outer(cos(u), sin(v)) + cx
        tris[:,:,1] = r * outer(sin(u), sin(v)) + cy
        tris[:,:,2] = r * outer(ones(size(u)), cos(v)) + cz

        return tris

    def CalculateSpherMesh(self,spher,sampleno=100,angleu=[0,pi],anglev=[0,2*pi]):
        # Definition to calculate triangular meshed form of a spherical sufrace.
        cx = spher[0]; cy = spher[1]; cz = spher[2]; r = spher[3]
        v           = linspace(angleu[0], angleu[1], sampleno)
        u           = linspace(anglev[0],anglev[1],sampleno)
        tris        = zeros((sampleno,sampleno,3))
        tris[:,:,0] = r * outer(cos(u), sin(v)) + cx
        tris[:,:,1] = r * outer(sin(u), sin(v)) + cy
        tris[:,:,2] = r * outer(ones(size(u)), cos(v)) + cz

        return tris

    def CalculateFocal(self,rx,ry,rz,n,ShowFocal=False):
        # Method to calculate the focal length of the lens in different axes.
        for a in [rx,ry]:
            R         = (pow(a,2)+pow(rz,2))/(2*rz)
            LensMaker = (n-1)*(-2/R+(n-1)*rz*2/(n*R))
            f         = pow(LensMaker,-1)
            if ShowFocal == True:
                print 'Focal length of the lens: ',f

        return True

    def PlotMesh(self,tris,alpha=0.3):
        # Definition to plot meshes using triangles.
        sampleno = tris.shape[0]
        for i in xrange(0,sampleno-1):
            for j in xrange(0,sampleno-1):
                self.plottriangle(tris[i,j],tris[i+1,j],tris[i,j+1],alpha=alpha)
                self.plottriangle(tris[i+1,j+1],tris[i+1,j],tris[i,j+1],alpha=alpha)

        return tris

    def FindInterMesh(self,vector,tris,RangeWindow=None,s=2):
        # Definition to find the first intersection of a ray with a mesh.
        sampleno = tris.shape[0]
        if RangeWindow == None:
            limin = 0; limax=sampleno-1
            ljmin = 0; ljmax=sampleno-1
        else:
            limin = RangeWindow[0][0]; limax = RangeWindow[0][1]
            ljmin = RangeWindow[1][0]; ljmax = RangeWindow[1][1]
        for i in xrange(limin,limax):
            for j in xrange(ljmin,ljmax):
                tri0        = [tris[i,j],tris[i+1,j],tris[i,j+1]]
                tri1        = [tris[i+1,j+1],tris[i+1,j],tris[i,j+1]]
                s0,normvec0 = self.findintersurface(vector,(tri0[0],tri0[1],tri0[2]))
                res0        = self.isitontriangle(normvec0[0],tri0[0],tri0[1],tri0[2])
                if res0 == True:
                    return s0,normvec0,tri0,[[i-s,i+s],[j-s,j+s]]
                s1,normvec1 = self.findintersurface(vector,(tri1[0],tri1[1],tri1[2]))
                res1        = self.isitontriangle(normvec1[0],tri1[0],tri1[1],tri1[2])
                if res1 == True:
                    return s1,normvec1,tri1,[[i-s,i+s],[j-s,j+s]]

        return 0,None,None,None

    def PlotCircle(self,center,r,c='none'):
        # Method to plot circle.
        circle = Circle((center[0], center[1]), r, facecolor=c,
                        edgecolor=(0,0,0), linewidth=4, alpha=1)
        
        self.ax.add_patch(circle)
        art3d.pathpatch_2d_to_3d(circle, z=center[2], zdir='z')
        return array([center,r])

    def PlotData(self,X,Y,Z,c='none'):
        # Method to plot the given data.
        # Gridding the data.
        xi = linspace(min(X), max(X))
        yi = linspace(min(Y), max(Y))
        xim, yim = meshgrid(xi, yi)
        zi = griddata(X,Y,Z,xi,yi,interp='nn')
        # Plot the resultant figure.
        self.ax  = self.fig.gca()
        self.ax.plot_surface(xim, yim, zi, rstride=2, cstride=2,
                             cmap=cm.jet, alpha=0.3, color=c)

        return True

    def plottriangle(self,point0,point1,point2,alpha=0.3):
        # Method to plot triangular surface
        x     = array([ point0[0], point1[0], point2[0]])
        y     = array([ point0[1], point1[1], point2[1]])
        z     = array([ point0[2], point1[2], point2[2]])
        verts = [zip(x, y,z)]

        self.ax.add_collection3d(Poly3DCollection(verts,alpha=alpha))
        return array([point0,point1,point2])

    def plotcornercube(self,centerx,centery,centerz,pitch,revert=False):
        # Method to plot a single cornercube
        point00 = array([ centerx, centery, centerz])
        point10 = array([ centerx, centery, centerz])
        point20 = array([ centerx, centery, centerz])
        if revert == False:
            point01 = array([ centerx, centery-2*pitch/3, centerz+sqrt(2)*pitch/3 ])
            point11 = array([ centerx, centery-2*pitch/3, centerz+sqrt(2)*pitch/3 ])
            point21 = array([ centerx-pitch/sqrt(3), centery+pitch/3,
                              centerz+sqrt(2)*pitch/3 ])
            point02 = array([ centerx-pitch/sqrt(3), centery+pitch/3,
                              centerz+sqrt(2)*pitch/3 ])
            point12 = array([ centerx+pitch/sqrt(3), centery+pitch/3,
                              centerz+sqrt(2)*pitch/3 ])
            point22 = array([ centerx+pitch/sqrt(3), centery+pitch/3,
                              centerz+sqrt(2)*pitch/3 ])
        else:
            point01 = array([ centerx, centery+2*pitch/3, centerz+sqrt(2)*pitch/3 ])
            point11 = array([ centerx, centery+2*pitch/3, centerz+sqrt(2)*pitch/3 ])
            point21 = array([ centerx+pitch/sqrt(3), centery-pitch/3,
                              centerz+sqrt(2)*pitch/3 ])
            point02 = array([ centerx+pitch/sqrt(3), centery-pitch/3,
                              centerz+sqrt(2)*pitch/3 ])
            point12 = array([ centerx-pitch/sqrt(3), centery-pitch/3,
                              centerz+sqrt(2)*pitch/3 ])
            point22 = array([ centerx-pitch/sqrt(3), centery-pitch/3,
                              centerz+sqrt(2)*pitch/3 ])

        self.plottriangle(point00,point01,point02)
        self.plottriangle(point10,point11,point12)
        self.plottriangle(point20,point21,point22)

        return array([point00,point01,point02]), \
            array([point10,point11,point12]), \
            array([point20,point21,point22])

    def defineplotshape(self,(xmin,xmax),(ymin,ymax),(zmin,zmax)):
        # Method to define plot shape.
        self.ax.set_xlim3d(xmin,xmax)
        self.ax.set_ylim3d(ymin,ymax)
        self.ax.set_zlim3d(zmin,zmax)

        return True

    def SavePlot(self,filename):
        # Definition to save the plotted figure. One should call it after showplot.
        self.plt.savefig(filename,bbox_inches='tight')

        return True

    def showplot(self,title=None,LabelX=None,LabelY=None,filename=None,
                 plot2d=False):
        
        # Shows the prepared plot
        print LabelX        
        print filename
        if title != None or LabelX != None or LabelY != None:
            self.plt.title(title)
            self.plt.xlabel(LabelX)
            self.plt.ylabel(LabelY)

        
            
        if not plot2d:
            #self.ax.view_init(10.0, -135.0)
            self.ax.view_init(0.0, 270.0)
            self.plt.xlabel('X')
            self.plt.ylabel('Y')

        if filename != None:
            self.SavePlot(filename)

        self.plt.show()

        self.CloseFigure()
        return True

    def CloseFigure(self):
        # Method to close the last figure.
        self.plt.close()
        return True

    def CloseAllFigures(self):
        # Method to close all figures.
        self.plt.close('all')
        return True

    
####################################################################
class ParaxialMatrix():

    def __init__(self):
        # See "Laser beams and resonators" from Kogelnik and Li for
        # the theoratical explanation

        self.plt = matplotlib.pyplot
        self.fig = self.plt.figure()
        self.ax  = self.fig.add_subplot(111,aspect='equal')
        # Show grid.
        self.plt.grid()

        return

    def CreateVector(self,x,angle):
        # Creates a paraxial ray, angle is in degrees, x is
        # the distance of the point to the plane of direction of propagation
        angle  = radians(angle)
        vector = array([[x],[tan(angle)],[1]])

        return vector

    def FreeSpace(self,vector,distance,deltax=0,deltafi=0):
        # Ray transfer matrix of free space propagation, distance is in milimeters.
        # deltax is the spatial shift, deltafi is the angular shift.
        space  = array([[1,distance,deltax],[0,1,deltafi],[0,0,1]])
        vector = dot(space,vector)

        return vector

    def CurvedInterface(self,vector,n1,n2,R,deltax=0,deltafi=0):
        # Ray transfer matrix of a curved interface,
        # focal length is f and is in in milimeters.
        # Taken from Wikipedia article: Ray transfer matrix anaylsis.
        # deltax is the spatial shift, deltafi is the angular shift.
        # n1 is the first medium that the ray is coming from.
        # n2 is the second medium that the ray is entering to.
        # R is the radius of curvature, R>0 for convex
        CInter = array([[1,0,deltax],[(n1-n2)/R/n2,n1/n2,deltafi],[0,0,1]])
        vector = dot(CInter,vector)
        return vector

    def PlotVector(self,startvector,stopvector,posx=0,distance=0,color='g+-'):
        if stopvector[1] !=0:
            # Method to plot paraxial vectors in 2D space.
            self.plt.plot([posx,(stopvector[0]-startvector[0])\
                           /stopvector[1]+posx],[startvector[0],stopvector[0]],color)
            # Return new position at X-axis.
            posx += (stopvector[0]-startvector[0])/stopvector[1]
        else:
            self.plt.plot([posx,posx+distance],[startvector[0],stopvector[0]],color)
            posx = distance
        return posx
    def PlotLine(self,point1,point2,color='ro--'):
        # Definition to plot a line in between two points.
        self.plt.plot(point1,point2,color)

        return True

    def PlotLens(self,CenterXY, thickness, LensHeight, rotation, alpha=0.5):
        # Definition to plot a lens.
        lens = Ellipse(xy=CenterXY, width=thickness,
                       height=LensHeight, angle=-rotation)
        
        self.ax.add_artist(lens)
        lens.set_clip_box(self.ax.bbox)
        lens.set_alpha(alpha)
        
        return True
    
    def InitNewPlot(self):
        # New plot initiated.
        NewFig  = self.plt.figure()
        NewPlot = NewFig.add_subplot(111)
        return NewPlot,NewFig

    def PlotHist(self,dataset,plot):
        # Definition to plot a histogram.
        plot.hist(dataset,bins=1000,color='blue',normed='True')

        return True

    def PlotData(self,dataset,color,alpha=1,linestyle='-'):
        # Definition to plot a dataset.
        self.plt.plot(dataset[0],dataset[1],linestyle=linestyle,
                      color=color,alpha=alpha)
        return True
    
    def PlotFillData(self,dataset,color):
        # Definition to plot a dataset with fill.
        self.plt.fill(dataset[0],dataset[1],color,alpha=0.3)
        
        return True
    
    def ShowPlot(self):
        # Definition to plot the result.
        self.plt.show()
        
        return True



####################################################################
class jonescalculus():

    def __init__(self):
        return
    
    def linearpolarizer(self,input,rotation=0):
        # Linear polarizer, rotation is in degrees and it is counter clockwise
        rotation        = radians(rotation)
        rotmat          = array([[cos(rotation),sin(rotation)],
                                 [-sin(rotation),cos(rotation)]])
        
        linearpolarizer = array([[1,0],[0,0]])
        linearpolarizer = dot(rotmat.transpose(),dot(linearpolarizer,rotmat))

        return dot(linearpolarizer,input)
    
    def circullarpolarizer(self,input,type='lefthanded'):
        # Circullar polarizer
        if type == 'lefthanded':
            circullarpolarizer = array([[0.5,-0.5j],[0.5j,0.5]])
        if type == 'righthanded':
            circullarpolarizer = array([[0.5,0.5j],[-0.5j,0.5]])
            
        return dot(circullarpolarizer,input)
    
    def quarterwaveplate(self,input,rotation=0):
        # Quarter wave plate, type determines the placing of the fast axis
        rotation = radians(rotation)
        rotmat   = array([[cos(rotation),sin(rotation)],
                          [-sin(rotation),cos(rotation)]])
        
        qwp = array([[1,0],[0,-1j]])
        qwp = dot(rotmat.transpose(),dot(qwp,rotmat))

        return dot(qwp,input)
    
    def halfwaveplate(self,input,rotation=0):
        # Half wave plate
        rotation = radians(rotation)
        rotmat   = array([[cos(rotation),sin(rotation)],
                          [-sin(rotation),cos(rotation)]])
        
        hwp      = array([[1,0],[0,-1]])
        hwp      = dot(rotmat.transpose(),dot(hwp,rotmat))
        
        return dot(hwp,input)

    def waveplate(self,input,retardation=0,rotation=0):
        # Waveplate with a given retardation angle.
        rotation    = radians(rotation)
        retardation = 2*radians(retardation)
        rotmat      = array([[cos(rotation),sin(rotation)],[-sin(rotation),cos(rotation)]])
        wp          = array([[1,0],[0,exp(-1j*retardation)]])
        wp          = dot(rotmat.transpose(),dot(wp,rotmat))
        return dot(wp,input)
    def birefringentplate(self,input,nx,ny,d,wavelength,rotation=0):
        # Birefringent plate, d thickness, nx and ny refractive indices
        rotation = radians(rotation)
        rotmat   = array([[cos(rotation),sin(rotation)],[-sin(rotation),cos(rotation)]])
        delta    = 2*pi*(nx-ny)*d/wavelength
        bfp      = array([[1,0],[0,exp(-1j*delta)]])
        bfp      = dot(rotmat.transpose(),dot(bfp,rotmat))
        return dot(bfp,input)

    def LCD(self,input,alpha,ne,n0,d,wavelength,rotation=0):
        # THIS DEFINITION IS DEFECTED, DO NOT USE IT!
        # Nematic liquid crystal, d cell thickness, extraordinary refrative index ne, ordinary refractive index n0,
        # alpha helical twist per meter in right-hand sense along the direction of wave propagation
        # alpha is calculated is by dividing cell thickness to 1 meter length
        # alpha    =  1 /d
        #http://books.google.com/books?id=0XhtwBpMtA8C&lpg=PA208&ots=t8NlS2vuDP&dq=TN%20LC%20jones%20matrix&hl=tr&pg=PA209#v=onepage&q=TN%20LC%20jones%20matrix&f=false
        rotation = radians(rotation)
        rotmat   = array([[cos(rotation),sin(rotation)],[-sin(rotation),cos(rotation)]])
        gamma    = 2*pi*(ne-n0)/wavelength*d
        desangle = 90.
        N        = desangle/gamma
        print gamma, N
        lrot     = array([[cos(alpha*d),-sin(alpha*d)],[sin(alpha*d),cos(alpha*d)]])
        lretard  = array([[exp(-1j*gamma/2/N),0],[0,exp(1j*gamma/2/N)]])
        #llcd     =
        lc       = dot(lrot,lcd)
        lc       = dot(rotmat.transpose(),dot(lc,rotmat))
        
        return dot(lc,input)
    
    def ferroliquidcrystal(self,input,tetat,ne,n0,d,
                           wavelength,fieldsign='+',rotation=0):
        
        # Ferroelectric liquid crystal, d cell thickness,
        # extraordinary refrative index ne, ordinary refractive index
        # n0 Applied field sign determines the rotation angle
        
        rotation = radians(rotation)
        tetat    = radians(tetat)
        rotmat   = array([[cos(rotation),sin(rotation)],
                          [-sin(rotation),cos(rotation)]])
        
        beta     = 2*pi*(ne-n0)/wavelength
        lrot1    = array([[cos(tetat),-sin(tetat)],[sin(tetat),cos(tetat)]])
        lrot2    = array([[cos(tetat),sin(tetat)],[-sin(tetat),cos(tetat)]])
        lretard  = array([[1,0],[0,exp(-1j*beta*d)]])
        if fieldsign == '+':
            lc = dot(dot(lrot1,lretard),lrot2)
        elif fieldsign == '-':
            lc = dot(dot(lrot2,lretard),lrot1)
        lc       = dot(rotmat.transpose(),dot(lc,rotmat))
        
        return dot(lc,input)
    
    def electricfield(self,a1,a2):
        # Electric field vector is defined here.
        # a1 is the electic field intensity at x-axis.
        # a2 is the electric field intensity at y-axis.

        return array([[a1],[a2]])

####################################################################
class aperture():

    def __init__(self):
        self.plt = matplotlib.pyplot
        return

    def twoslits(self,nx,ny,X,Y,delta):
        # Creates a matrix that contains two slits
        obj=zeros((nx,ny),dtype=complex)
        for i in range(int(nx/2-X/2),int(nx/2+X/2)):
            for j in range(int(ny/2+delta/2-Y/2),int(ny/2+delta/2+Y/2)):
                obj[ny/2-abs(ny/2-j),i] = 1
                obj[j,i] = 1

        return obj
    

    def rectangle(self,nx,ny,side):
        # Creates a matrix that contains rectangle
        obj=zeros((nx,ny),dtype=complex)
        for i in range(int(nx/2-side/2),int(nx/2+side/2)):
            for j in range(int(ny/2-side/2),int(ny/2+side/2)):
                obj[j,i] = 1
                
        return obj

    def circle(self,nx,ny,radius):
        # Creates a matrix that contains circle
        obj=zeros((nx,ny),dtype=complex)
        for i in range(int(nx/2-radius/2),int(nx/2+radius/2)):
            for j in range(int(ny/2-radius/2),int(ny/2+radius/2)):
                if (abs(i-nx/2)**2+abs(j-ny/2)**2)**(0.5)< radius/2:
                    obj[j,i] = 1
                    
        return obj

    def sinamgrating(self,nx,ny,grating):
        # Creates a sinuosidal grating matrix
        obj=zeros((nx,ny),dtype=complex)
        for i in xrange(nx):
            for j in xrange(ny):
                obj[i,j] = 0.5+0.5*cos(2*pi*j/grating)
                
        return obj

    def lens(self,nx,ny,focal,wavelength,pixeltom):
        # Creates a lens matrix
        obj    = zeros((nx,ny),dtype=complex)
        k      = 2*pi/wavelength
        x      = linspace(-nx*pixeltom,nx*pixeltom,nx)
        y      = linspace(-ny*pixeltom,ny*pixeltom,ny)
        X,Y    = meshgrid(x,y)
        Z      = X**2+Y**2
        obj    = exp(-1j*k*0.5/focal*Z)
        
        return obj

    def gaussian(self,nx,ny,sigma):
        # Creates a 2D gaussian matrix
        obj = zeros((nx,ny),dtype=complex)
        for i in xrange(nx):
            for j in xrange(ny):
                obj[i,j] = 1/pi/pow(sigma,2)* \
                           exp(-float(pow(i-nx/2,2)+ pow(j-ny/2,2))/2/pow(sigma,2))

        return obj

    def retroreflector(self,nx,ny,wavelength,pitch,type='normal'):
        if nx != ny:
           nx = max([nx,ny])
           ny = nx
        part  = zeros((pitch,int(pitch/2)))
        for i in xrange(int(sqrt(3)*pitch/6)):
            for j in xrange(int(pitch/2)):
                if float(j)/(int(sqrt(3)*pitch/6)-i) < sqrt(3):
                    part[i,j]       = int(sqrt(3)*pitch/6)-i
                    part[pitch-i-1,int(pitch/2)-j-1] = part[i,j]
        for i in xrange(int(pitch)):
            for j in xrange(int(pitch/2)):
                if j != 0:
                    if float(j)/(int(pitch)-i) < 0.5 and \
                       (int(sqrt(3)*pitch/6)-i)/float(j) < 1./sqrt(3):
                        
                        # Distance to plane determines the level of the amplitude
                        # Plane as a line y = slope*x+ pitch
                        # Perpendicula line  y = -(1/slope)*x+n
                        slope     = -0.5
                        n         = j + (1/slope) * (i)
                        x1        = (n - pitch/2)/(slope+1/slope)
                        y1        = -(1/slope)*x1+n
                        part[i,j] = int(sqrt(3)*pitch/6) - \
                                    sqrt( pow(i-x1,2) + pow(j-y1,2) )
                        
                        part[pitch-i-1,int(pitch/2)-j-1] = part[i,j]
                else:
                    if i > int(sqrt(3)*pitch/6):
                        slope     = -0.5
                        n         = j + (1/slope) * (i)
                        x1        = (n - pitch/2)/(slope+1/slope)
                        y1        = -(1/slope)*x1+n
                        part[i,j] = int(sqrt(3)*pitch/6) - \
                                    sqrt( pow(i-x1,2) + pow(j-y1,2) )
                        
                        part[pitch-i-1,int(pitch/2)-j-1] = part[i,j]
        left  = part
        right = part[::-1]
        part  = append(left,right,axis=1)
        obj   = tile(part,(nx/pitch,ny/pitch))

        for i in xrange(nx/pitch/2):
           obj[(2*i+1)*pitch:(2*i+1)*pitch+pitch,:] = roll(
               obj[(2*i+1)*pitch:(2*i+1)*pitch+pitch,:],pitch/2)
           
        k     = 2*pi/wavelength
        D     = 5
        obj   = pow(obj,3)*exp(1j*k*obj)
        
        return obj

    def show(self,obj,pixeltom,wavelength,title='Detector',
             type='normal',filename=None,xlabel=None,ylabel=None):

        # Plots a detector showing the given object
        self.plt.figure(),self.plt.title(title)
        nx,ny = obj.shape
        # Number of the ticks to be shown both in x and y axes
        if type == 'normal':
            obj = abs(obj)
        elif type == 'log':
            obj = log(abs(obj))
        img = self.plt.imshow(obj,cmap=matplotlib.cm.jet,origin='lower')
        self.plt.colorbar(img,orientation='vertical')
        self.plt.xlabel(xlabel)
        self.plt.ylabel(ylabel)
        if filename != None:
            self.plt.savefig(filename)
            
        return True

    def show3d(self,obj,filename=None):
        nx,ny   = obj.shape
        fig     = self.plt.figure()
        ax      = fig.gca(projection='3d')
        X,Y     = mgrid[0:nx,0:ny]
        surf    = ax.plot_surface(
            X,Y,abs(obj), rstride=1, cstride=1, cmap=matplotlib.cm.jet,
            linewidth=0, antialiased=False)

        fig.colorbar(surf, shrink=0.5, aspect=5)
        if filename != None:
            self.plt.savefig(filename)

        return True
    def showrow(self,obj,wavelength,pixeltom,distance,filename=None):
        # Plots row crosssection of the given object
        nx,ny = obj.shape
        a     = 5
        self.plt.figure()
        self.plt.plot(arange(-nx/2,nx/2)*pixeltom,abs(obj[nx/2,:]))
        if filename != None:
            self.plt.savefig(filename)

        return True
    
    def showplots(self):
        # Definition to show the plots.
        self.plt.show()
        
        return True
    
    def ClosePlot(self):
        # Definition to kill a figure.
        self.plt.close("all")
        
        return True

####################################################################
class beams():

    def __init(self):
        self.plt = matplotlib.pyplot
        return
    def spherical(self,nx,ny,distance,wavelength,pixeltom,focal,amplitude=1):
        # Spherical wave
        distance = abs(focal-distance)
        k        = 2*pi/wavelength
        X,Y      = mgrid[-nx/2:nx/2,-ny/2:ny/2]*pixeltom
        r        = sqrt(pow(X,2)+pow(Y,2)+pow(distance,2))
        U        = amplitude/r*exp(-1j*k*r)
        return U
    def gaussian(self,nx,ny,distance,wavelength,pixeltom,amplitude,waistsize,focal=0):
        # Gaussian beam
        distance = abs(distance-focal)
        X,Y      = mgrid[-nx/2:nx/2,-ny/2:ny/2]*pixeltom
        ro       = sqrt(pow(X,2)+pow(Y,2))
        z0       = pow(waistsize,2)*pi/wavelength
        A0       = amplitude/(1j*z0)
        if distance == 0:
            U = A0*exp(-pow(ro,2)/pow(waistsize,2))
            return U
        k        = 2*pi/wavelength
        R        = distance*(1+pow(z0/distance,2))
        W        = waistsize*sqrt(1+pow(distance/z0,2))
        ksi      = 1./arctan(distance/z0)
        U        = A0*waistsize/W*exp(-pow(ro,2)/pow(W,2))*exp(-1j*k*distance-1j*pow(ro,2)/2/R+1j*ksi)
        return U
    def multiplication(self,wave,aperture):
        # Definition to multiply a wave with an aperture.
        return  multiply(wave,aperture)

class diffractions():
    def __init__(self):
        return

    def fft(self,obj):
        return fftshift(fft2(obj))

    def fresnelfraunhofer(self,wave,wavelength,distance,
                          pixeltom,aperturesize,type='Fresnel'):

        # Definitions for Fresnel impulse respone (IR),
        # Fresnel Transfer Function (TF), Fraunhofer diffraction.
        # According to "Computational Fourier Optics" by David Vuelz.

        nu,nv  = wave.shape
        k      = 2*pi/wavelength
        x      = linspace(-nu*pixeltom,nu*pixeltom,nu)
        y      = linspace(-nv*pixeltom,nv*pixeltom,nv)
        X,Y    = meshgrid(x,y)
        Z      = X**2+Y**2
        if type == 'Fresnel':
            smplng = wavelength*distance/(aperturesize*pixeltom)
            if pixeltom < smplng: # Fresnel Impulse Response
                h      = 1./(1j*wavelength*distance)*exp(1j*k*0.5/distance*Z)
                h      = fft2(fftshift(h))*pixeltom**2
                print 'IR Fresnel method'
            else: # Fresnel Transfer Function
                h      = exp(1j*k*distance)*exp(-1j*pi*wavelength*distance*Z)
                h      = fftshift(h)
                print 'TR Fresnel method'
            U1     = fft2(fftshift(wave))
            U2     = h*U1
            result = ifftshift(ifft2(U2))
        elif type == 'Fraunhofer':
            c      = 1./(1j*wavelength*distance)*exp(1j*k*0.5/distance*Z)
            result = c*ifftshift(fft2(fftshift(wave)))*pixeltom**2
        return result

    def SuggestType(self,aperturesize,pixeltom,wavelength,distance):
        # Definition to suggest, which type of propagation would be meaningful.
        fresnelno    = self.fresnelnumber(aperturesize,pixeltom,wavelength,distance)
        if fresnelno < 0.001:
            type = 'Fraunhofer'
        else:
            type = 'Fresnel'
        print 'Fresnel number: %s, Propagation type: %s' % (fresnelno,type)
        return type,fresnelno

    def fresnelnumber(self,aperturesize,pixeltom,wavelength,distance):
        # Definition to calculate the fresnel number.
        return  pow(aperturesize*pixeltom,2)/wavelength/distance

    def intensity(self,obj):
        # Definition to calcualte the intensity of the given value.
        return abs(obj**2)

    def phase(self,obj):
        # Definition to show the phase of the given wave.
        return angle(obj)

    def transmittance(self,wave,trans):
        # Definition to calculate the output of a given input wave
        # through a transmittance function.
        return multiply(wave,trans)

    def FWHM (self,Irow):
        # Definition to calculate full width at half maximum of a
        # gaussian alike function.
        I  = Irow/sum(Irow) # Normalizing std
        return 2*sqrt(2*log(2))*std(I)

def main():
    print 'Odak by %s' % __author__
    return True

if __name__ == '__main__':
    sys.exit(main())
