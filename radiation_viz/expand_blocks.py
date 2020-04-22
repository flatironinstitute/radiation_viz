import numpy as np
from bisect import bisect_right, bisect_left

#np.set_printoptions(6, suppress=True)

def ar(*values):
    return np.array(values, dtype=np.float)

vertex_coefficients = np.zeros((8,8), dtype=np.float)

for i in range(2):
    for j in range(2):
        for k in range(2):
            index = i * 4 + j * 2 + k
            x = i*2 - 1
            y = j*2 - 1
            z = k*2 - 1
            vertex_coefficients[0, index] = x * y * z
            vertex_coefficients[1, index] = x * y
            vertex_coefficients[2, index] = x * z
            vertex_coefficients[3, index] = y * z
            vertex_coefficients[4, index] = x
            vertex_coefficients[5, index] = y
            vertex_coefficients[6, index] = z
            vertex_coefficients[7, index] = 1

def interpolate_corners(corner_values, xyz_offset):
    assert corner_values.shape == (2,2,2)
    #assert xyz_offset.shape == (3,)
    rcorners = corner_values.ravel()
    matrix = vertex_coefficients.copy()
    for i in range(8):
        matrix[:, i] = rcorners[i] * vertex_coefficients[:, i]
    #print ("matrix")
    #print(matrix)
    xyz_centered = 2 * xyz_offset - 1
    (x,y,z) = xyz_centered
    terms = np.array([x*y*z, x*y, x*z, y*z, x, y, z, 1.0], dtype=np.float)
    #print("terms")
    #print(terms)
    summands = (matrix.T).dot(terms.T)
    #print("summands")
    #print(summands)
    return summands.sum() / 8.0

def test_corners0():
    for x_offset in (0,1):
        for y_offset in (0,1):
            for z_offset in (0,1):
                xyz_offset = np.array([x_offset, y_offset, z_offset], dtype=np.float)
                corner_values = (np.arange(8)).reshape((2,2,2)) + x_offset *3 + y_offset * 7 + z_offset * 2 - 2
                test_value = x_offset + y_offset * 3 + z_offset * 5 - 12
                corner_values[x_offset, y_offset, z_offset] = test_value
                interp = interpolate_corners(corner_values, xyz_offset)
                if abs(interp - test_value) > 1e-10:
                    raise ValueError("%s expected %s but got %s" % (xyz_offset, test_value, interp))
                print (xyz_offset, test_value)
    print ("all ok")

def test_center():
    for x_offset in (0,1):
        for y_offset in (0,1):
            for z_offset in (0,1):
                xyz_offset = np.array([0.5, 0.5, 0.5], dtype=np.float)
                corner_values = (np.arange(8)).reshape((2,2,2)) + x_offset *3 + y_offset * 7 + z_offset * 2 - 2
                test_value = corner_values.mean()
                interp = interpolate_corners(corner_values, xyz_offset)
                if abs(interp - test_value) > 1e-10:
                    raise ValueError("%s expected %s but got %s" % (xyz_offset, test_value, interp))
                print (xyz_offset, test_value)
    print ("all ok")

class BlockInterpolator:
    
    def __init__(self, block, x_offsets, y_offsets, z_offsets):
        (self.block, self.x_offsets, self.y_offsets, self.z_offsets) = (block, x_offsets, y_offsets, z_offsets)
        #self.offsets = [x_offsets, y_offsets, z_offsets]
        self.delta_x = x_offsets[1:] - x_offsets[:-1]
        self.delta_y = y_offsets[1:] - y_offsets[:-1]
        self.delta_z = z_offsets[1:] - z_offsets[:-1]
        (nx, ny, nz) = block.shape
        self.mins = ar(x_offsets[0], y_offsets[0], z_offsets[0])
        self.maxes = ar(x_offsets[nx-1], y_offsets[ny-1], z_offsets[nz-1])

    def lower_border(self):
        "hash lookup along minimum x,y,z values"
        (block, x_offsets, y_offsets, z_offsets) = (self.block, self.x_offsets, self.y_offsets, self.z_offsets)
        (nx, ny, nz) = block.shape
        border = {}
        k = 0
        for i in range(nx):
            for j in range(ny):
                border[(x_offsets[i], y_offsets[j], z_offsets[k])] = block[i,j,k]
        j = 0
        for i in range(nx):
            for k in range(nz):
                border[(x_offsets[i], y_offsets[j], z_offsets[k])] = block[i,j,k]
        i = 0
        for k in range(nz):
            for j in range(ny):
                border[(x_offsets[i], y_offsets[j], z_offsets[k])] = block[i,j,k]
        return border
        
    def expand(self, interpolator):
        old_block = self.block
        (nx, ny, nz) = old_block.shape
        (nx1, ny1, nz1) = (nx-1, ny-1, nz-1)
        new_block = np.zeros((nx+1, ny+1, nz+1), dtype=np.float)
        def new_offsets(old_offsets):
            ln = old_offsets.shape[0]
            result = np.zeros(ln+1)
            result[:ln] = old_offsets
            result[ln] = old_offsets[-1]  # keep consistency for now.
            return result
        new_x_offsets = new_offsets(self.x_offsets)
        new_y_offsets = new_offsets(self.y_offsets)
        new_z_offsets = new_offsets(self.z_offsets)
        # fill in new block
        new_block[:nx, :ny, :nz] = old_block
        # interpolate expanded boundary
        def interpolate(i, j, k):
            default = old_block[min(i, nx1), min(j, ny1), min(k, nz1)]
            new_block[i, j, k] = interpolator(
                ar(new_x_offsets[i], new_y_offsets[j], new_z_offsets[k]),
                default)
        for i in range(nx+1):
            for j in range(ny+1):
                interpolate(i, j, nz)
        for i in range(nx+1):
            for k in range(nz+1):
                interpolate(i, ny, k)
        for k in range(nz+1):
            for j in range(ny+1):
                interpolate(nx, j, k)
        return BlockInterpolator(new_block, new_x_offsets, new_y_offsets, new_z_offsets)
        
    def info(self):
        print ("x", self.x_offsets)
        print ("y", self.y_offsets)
        print ("z", self.z_offsets)
        print (self.block)
        
    def in_range(self, xyz):
        # profiling indicates this is a hot spot
        #return np.all(self.mins <= xyz) and np.all(self.maxes > xyz)
        mins = self.mins
        maxes = self.maxes
        for i in range(3):
            v = xyz[i]
            if mins[i] > v: return False
            if maxes[i] <= v: return False
        return True
    
    def interpolate(self, xyz):
        block = self.block
        (nx, ny, nz) = block.shape
        (x, y, z) = xyz
        def offset(x, x_offsets, delta_x, nx):
            ix = bisect_right(x_offsets, x)
            dx = None
            if ix > 0 and ix < nx:
                dx = (x - x_offsets[ix-1]) / delta_x[ix-1]
            #print("ix, dx, nx", ix, dx, nx, x_offsets)
            return (ix, dx)
        (ix, dx) = offset(x, self.x_offsets, self.delta_x, nx)
        (iy, dy) = offset(y, self.y_offsets, self.delta_y, ny)
        (iz, dz) = offset(z, self.z_offsets, self.delta_z, nz)
        if dx is not None and dy is not None and dz is not None:
            corner_values = block[ix-1: ix+1, iy-1: iy+1, iz-1: iz+1]
            #print("corners")
            #print(corner_values)
            cxyz = ar(dx, dy, dz)
            #print("cxyz", cxyz)
            return interpolate_corners(corner_values, cxyz)
        else:
            return None # no interpolation in this block
        
    def __lt__(self, other):
        return self.mins[0] < other.mins[0]

""" HISTORICAL
class InterpolateBlocks:
    
    def __init__(self, block_interpolators, default=None, sort_index=1):
        blocks = block_interpolators
        self.sort_index = sort_index
        self.x_block_list = sorted((b.maxes[sort_index], b) for b in blocks)
        self.x_max_list = [x for (x,b) in self.x_block_list]
        self.last_block = blocks[0]
        M = blocks[0].block.max()
        for b in blocks:
            M = max(M, b.block.max())
        if default is None:
            self.default = M * 2 
        else:
            self.default = default
        #self.minimum = m
        
    def expand_all(self, verbose=False):
        "Expand all blocks and return summary structures"
        intensities = []
        x_values = []
        y_values = []
        z_values = []
        expanded = []
        count = 0
        for (x, b) in self.x_block_list:
            if verbose:
                count += 1
                print("block", count, b.block.shape)
            eb = b.expand(self.interpolate)
            expanded.append(eb)
            x_values.append(eb.x_offsets)
            y_values.append(eb.y_offsets)
            z_values.append(eb.z_offsets)
            intensities.append(eb.block)
        intensities = np.array(intensities, dtype=np.float)
        x_values = np.array(x_values, dtype=np.float)
        y_values = np.array(y_values, dtype=np.float)
        z_values = np.array(z_values, dtype=np.float)
        return {
            "intensities": intensities,
            "x_values": x_values,
            "y_values": y_values,
            "z_values": z_values,
            "blocks": expanded,
        }
        
    def interpolate(self, xyz, default=None, substitute=None):
        result = None
        # see if the last block still works
        block = self.last_block
        if (block is None) or (not block.in_range(xyz)):
            sort_index = self.sort_index
            block = None
            x_max_list = self.x_max_list
            x_block_list = self.x_block_list
            x = xyz[sort_index]
            start = bisect_right(x_max_list, x)
            for i in range(start, len(x_max_list)):
                (max_x, b) = x_block_list[i]
                if x >= max_x:
                    break
                if b.in_range(xyz):
                    block = b
                    break
        if block is not None:
            if substitute:
                result = substitute
            else:
                result = block.interpolate(xyz)
            assert result is not None
        elif default is not None:
            result = default
        self.last_block = block
        return result
"""

class InterpolateBlocks:

    # try to optimize lookups
    
    def __init__(self, block_interpolators, default=None):
        blocks = block_interpolators
        sort_index = 0
        self.x_block_list = sorted((b.maxes[sort_index], b) for b in blocks)
        maxes = blocks[0].maxes
        mins = blocks[0].mins
        borders = {}
        for b in blocks:
            maxes = np.maximum(maxes, b.maxes)
            mins = np.minimum(mins, b.mins)
            borders.update(b.lower_border())
        self.borders = borders
        self.border_hits = 0
        self.maxes = maxes
        self.mins = mins
        diff = maxes - mins
        self.diff = diff
        self.last_block = None
        max_dict3 = {}
        for b in blocks:
            (x,y,z) = b.maxes
            xdict = max_dict3.get(x, {})
            ydict = xdict.get(y, {})
            zlist = ydict.get(z, [])
            zlist.append(b)
            ydict[z] = zlist
            xdict[y] = ydict
            max_dict3[x] = xdict
        x_order = sorted(max_dict3.keys())
        self.x_order = x_order
        for x in x_order:
            xdict = max_dict3[x]
            y_order = sorted(xdict.keys())
            for y in y_order:
                ydict = xdict[y]
                z_order = sorted(ydict.keys())
                xdict[y] = (z_order, ydict)
            max_dict3[x] = (y_order, xdict)
        self.max_dict3 = max_dict3
        M = blocks[0].block.max()
        for b in blocks:
            M = max(M, b.block.max())
        if default is None:
            self.default = M * 2 
        else:
            self.default = default
        #self.minimum = m
        
    def expand_all(self, verbose=False):
        "Expand all blocks and return summary structures"
        intensities = []
        x_values = []
        y_values = []
        z_values = []
        expanded = []
        count = 0
        for (x, b) in self.x_block_list:
            if verbose:
                count += 1
                print("block", count, b.block.shape, self.border_hits)
            eb = b.expand(self.interpolate)
            expanded.append(eb)
            x_values.append(eb.x_offsets)
            y_values.append(eb.y_offsets)
            z_values.append(eb.z_offsets)
            intensities.append(eb.block)
        intensities = np.array(intensities, dtype=np.float)
        x_values = np.array(x_values, dtype=np.float)
        y_values = np.array(y_values, dtype=np.float)
        z_values = np.array(z_values, dtype=np.float)
        return {
            "intensities": intensities,
            "x_values": x_values,
            "y_values": y_values,
            "z_values": z_values,
            "blocks": expanded,
        }
        
    def interpolate(self, xyz, default=None, substitute=None):
        #print("b2 interpolating", xyz)
        # try to find in precomputed borders
        borders = self.borders
        txyz = tuple(xyz)
        hit = borders.get(txyz, None)
        if hit is not None:
            self.border_hits += 1
            return hit
        result = None
        # see if the last block still works
        block = self.last_block
        if (block is None) or (not block.in_range(xyz)):
            #print ("  last block fails", block)
            block = None
            (x, y, z) = xyz
            max_dict3 = self.max_dict3
            x_order = self.x_order
            max_dict3 = self.max_dict3
            startx = bisect_right(x_order, x)
            for i in range(startx, len(x_order)):
                Mx = x_order[i]
                if (Mx < x) or (block is not None):
                    break
                (y_order, xdict) = max_dict3[Mx]
                starty = bisect_right(y_order, y)
                for j in range(starty, len(y_order)):
                    My = y_order[j]
                    if (My < y) or (block is not None):
                        break
                    (z_order, y_dict) = xdict[My]
                    startz = bisect_right(z_order, z)
                    for k in range(startz, len(z_order)):
                        Mz = z_order[k]
                        if (Mz < z) or (block is not None):
                            break
                        zlist = y_dict[Mz]
                        for b in zlist:
                            if b.in_range(xyz):
                                block = b
        if block is not None:
            if substitute:
                result = substitute
            else:
                result = block.interpolate(xyz)
            assert result is not None
        elif default is not None:
            result = default
        self.last_block = block
        return result

"""historical
def interpolator_from_arrays(intensities, x_values, y_values, z_values):
     blocks = []
     for (index, chunk) in enumerate(intensities):
         x_chunk = x_values[index]
         y_chunk = y_values[index]
         z_chunk = z_values[index]
         b = BlockInterpolator(chunk, x_chunk, y_chunk, z_chunk)
         blocks.append(b)
     return InterpolateBlocks(blocks)
"""

def interpolator_from_arrays(intensities, x_values, y_values, z_values):
     blocks = []
     for (index, chunk) in enumerate(intensities):
         x_chunk = x_values[index]
         y_chunk = y_values[index]
         z_chunk = z_values[index]
         b = BlockInterpolator(chunk, x_chunk, y_chunk, z_chunk)
         blocks.append(b)
     return InterpolateBlocks(blocks)

