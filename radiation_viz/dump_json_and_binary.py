import h5py
import numpy as np
import json
import os
from . import expand_blocks

# save canvas as image
# https://stackoverflow.com/questions/28299050/how-to-use-filesaver-js-with-canvas/28305948

def a32(x):
    return np.array(x, dtype=np.float32)

class BlockDescriptions:

    def __init__(self, rs, thetas, phis, values):
        (nb, nr, nt, np) = values.shape
        (nb1, nr1) = rs.shape
        assert nb1 == nb and nr1 == nr + 1, repr((rs.shape, values.shape))
        (nb1, nt1) = thetas.shape
        assert nb1 == nb and nt1 == nt + 1, repr((thetas.shape, values.shape))
        (nb1, np1) = phis.shape
        assert nb1 == nb and np1 == np + 1, repr((phis.shape, values.shape))
        self.rs = rs
        self.thetas = thetas
        self.phis = phis
        self.values = values

    def interpolator(self):
        return expand_blocks.interpolator_from_arrays(self.values, self.rs, self.thetas, self.phis)

    def interp_data_cube(self, side, default=0.0, substitute=None, verbose=True):
        result = np.zeros((side, side, side), dtype=np.float)
        interp = self.interpolator()
        if verbose:
            print("interp", interp)
        def ticks(arr):
            M = arr.max()
            m = arr.min()
            d = M - m
            assert d > 1e-5, "difference in array too small " + repr((M, m, d))
            di = d / side
            return [(i, m + di * i) for i in range(side)]
        for (i,r) in ticks(self.rs):
            if verbose:
                print("at r", i, r)
            for (j,theta) in ticks(self.thetas):
                for (k,phi) in ticks(self.phis):
                    p = np.array([r, theta, phi], dtype=np.float)
                    result[i,j,k] = interp.interpolate(p, default, substitute=substitute)
        return result

    def dump_files(self, to_dir, to_prefix, indent=None, verbose=True):
        json_fn = to_prefix + ".json"
        bin_fn = to_prefix + ".bin"
        json_path = os.path.join(to_dir, json_fn)
        bin_path = os.path.join(to_dir, bin_fn)
        r_values = self.rs
        theta_values = self.thetas
        phi_values = self.phis
        values = self.values
        (num_blocks, r_size, theta_size, phi_size) = values.shape
        json_value = {
            "r_max": float(r_values.max()),
            "intensity_max": float(values.max()),
            "intensity_min": float(values.min()),
            "r_size": r_size,
            "theta_size": theta_size,
            "phi_size": phi_size,
            "num_blocks": num_blocks,
            "r_values": r_values.ravel().tolist(),
            "theta_values": theta_values.ravel().tolist(),
            "phi_values": phi_values.ravel().tolist(),
            "binary_file": bin_fn,
        }
        json_f = open(json_path, "w")
        json.dump(json_value, json_f, indent=indent)
        json_f.close()
        if verbose:
            print("    wrote json to", json_path)
        bin_f = open(bin_path, "wb")
        values.ravel().astype(np.float32).tofile(bin_f)
        bin_f.close()
        if verbose:
            print("    wrote binary to", bin_path)
        return(json_fn , bin_fn)

    def truncate_r_phi(self, skip, verbose=True):
        r_values = truncate(self.rs, skip)
        theta_values = self.thetas # truncate(self.thetas)
        phi_values = truncate(self.phis, skip)
        values = self.values[:, ::skip, :, ::skip]
        if verbose:
            print("    truncating", self.rs.shape, "by", skip)
            print ("   to", r_values.shape, theta_values.shape, phi_values.shape, values.shape)
        return self.__class__(r_values, theta_values, phi_values, values)

    def expand(self, verbose=True):
        interp = self.interpolator()
        e = interp.expand_all(verbose=verbose)
        return self.__class__(e["x_values"], e["y_values"], e["z_values"], e["intensities"], )

""" historical
class BlockDescriptions2(BlockDescriptions):

    def interpolator(self):
        return expand_blocks.interpolator_from_arrays2(self.values, self.rs, self.thetas, self.phis)
"""

def truncate(array, skip):
    (b, k) = array.shape
    indices = list(range(0, k, skip))
    #print (indices)
    shape2 = (b, len(indices))
    #print (shape2, array.shape)
    out = np.zeros(shape2, array.dtype)
    for i in indices:
        out[:,i//skip] = array[:, i]
    return out

"""
def get_values_and_geometry0(from_filename, source="prim", index=0, verbose=True):
    f = h5py.File(from_filename, 'r')
    rs = a32(f["x1f"][:])
    thetas = a32(f["x2f"][:])
    phis = a32(f["x3f"][:])
    values = f[source][:][index]
    if verbose:
        print (rs.shape, thetas.shape, phis.shape, values.shape)
    return BlockDescriptions(rs, thetas, phis, values)
"""

def copy_single_value(from_filename, to_filename, source="prim", index=0):
    "Create small data file with only intensity (eg) for testing/examples."
    f = h5py.File(from_filename, 'r')
    out = h5py.File(to_filename, 'w')
    phis = a32(f["x1f"][:])
    thetas = a32(f["x2f"][:])
    rs = a32(f["x3f"][:])
    values1 = a32(f[source][:][index])
    (bb, nphi, ntheta, nr) = values1.shape
    ext_values = values1.reshape((1, bb, nphi, ntheta, nr))
    out.create_dataset('x1f', data=phis)
    out.create_dataset('x2f', data=thetas)
    out.create_dataset('x3f', data=rs)
    out.create_dataset(source, data=ext_values)
    out.close()
    print("from", from_filename, "copied", source, index, "to", to_filename)

def get_values_and_geometry(from_filename, source="prim", index=0, verbose=True):
    f = h5py.File(from_filename, 'r')
    phis = a32(f["x1f"][:])
    thetas = a32(f["x2f"][:])
    rs = a32(f["x3f"][:])
    values1 = f[source][:][index]
    values = values1
    if 1:
        # don't know how to do this the smart way
        rs = a32(f["x1f"][:])
        thetas = a32(f["x2f"][:])
        phis = a32(f["x3f"][:])
        (bb, nphi, ntheta, nr) = values1.shape
        values = np.zeros((bb, nr, ntheta, nphi), dtype=np.float32)
        for b in range(bb):
            for ir in range(nr):
                for itheta in range(ntheta):
                    #for iphi in range(nphi):
                    #    values[b, ir, itheta, iphi] = values1[b, iphi, itheta, ir]
                    values[b, ir, itheta, :] = values1[b, :, itheta, ir]
    if verbose:
        print("from", from_filename, source, index)
        print (rs.shape, thetas.shape, phis.shape, values.shape)
    return BlockDescriptions(rs, thetas, phis, values)

def get_viz_values(from_filename, source="prim", index=0, verbose=True):
    f = h5py.File(from_filename, 'r')
    rs = a32(f["x1f"][:])
    thetas = a32(f["x2f"][:])
    phis = a32(f["x3f"][:])
    values1 = f[source][:][index]
    print("v", values1.shape, "r", rs.shape, "theta", thetas.shape, "phi", phis.shape)
    #values = values1.copy()
    # don't know how to do this the smart way
    (bb, nphi, ntheta, nr) = values1.shape
    values = np.zeros((bb, nr, ntheta, nphi), dtype=np.float32)
    for b in range(bb):
        for ir in range(nr):
            for itheta in range(ntheta):
                for iphi in range(nphi):
                    values[b, ir, itheta, iphi] = values1[b, iphi, itheta, ir]
    if verbose:
        print (rs.shape, thetas.shape, phis.shape, values.shape)
    return BlockDescriptions(rs, thetas, phis, values)

