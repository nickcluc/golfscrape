import math
def bearing_err(s,pin):
    # decompose end-pin vector relative to start->pin line
    sy,sx=s['startLat'],s['startLong']; ey,ex=s['endLat'],s['endLong']; py,px=pin
    k=math.cos(math.radians(py))
    ax,ay=(px-sx)*k,(py-sy); bx,by_=(ex-sx)*k,(ey-sy)
    L=math.hypot(ax,ay); 
    if L==0: return None
    ux,uy=ax/L,ay/L
    along=(bx*ux+by_*uy)-L; side=bx*uy-by_*ux  # side>0 => right of line
    f=111320*1.09361
    return along*f, side*f
