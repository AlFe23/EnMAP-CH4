# EnMAP-CH4

This repository contains the code and resources for detecting and quantifying methane (CH4) emissions **using EnMAP hyperspectral satellite imagery**.

The methodology, originally developed within the CLEAR-UP project funded by ASI, leverages EnMAP’s VNIR/SWIR imaging spectrometer and an enhanced matched-filter technique called **Cluster-Tuned Matched Filter (CTMF)**, applied to Level-1B radiance data. A scene-specific unit-absorption spectrum, generated from a MODTRAN-based lookup table (LUT), serves as the target signature in the matched filter, enabling methane detection in the 2300 nm absorption window. Column enhancements are converted to concentration (ppm·m) by linearly inverting the Beer–Lambert law.

Check also the implementation for PRISMA: [PRISMA-CH4](https://github.com/AlFe23/PRISMA-CH4/)


<div align="center">
<img src="https://github.com/user-attachments/assets/809c85dc-191e-4804-8a39-d27fcc3bf853" width="20%">
</div>


**Authors:** Alvise Ferrari, Giovanni Laneve 

**Contact:** alvise.ferrari@uniroma1.it, ferrarialvise@gmail.com, giovanni.laneve@uniroma1.it


**Citation:**

- Ferrari, A., Laneve, G., Tellez, R.A.C., Pampanoni, V., Saquella, S. and Guarini, R., 2025. Analysis of Local Methane Emissions Using Near-Simultaneous Multi-Satellite Observations: Insights from Landfills and Oil-Gas Facilities. arXiv preprint arXiv:2506.01113.

- A. Ferrari, G. Laneve, V. Pampanoni, A. Carvajal and F. Rossi, "Monitoring Methane Emissions from Landfills Using Prisma Imagery," IGARSS 2024 - 2024 IEEE International Geoscience and Remote Sensing Symposium, Athens, Greece, 2024, pp. 3663-3667, doi: 10.1109/IGARSS53475.2024.10642079.


**Links:**

- [Docker prisma-ch4-mapper.tar](https://drive.google.com/file/d/1-VDaMb_0o8FXf3nz5--XWq10yug3nXih/view?usp=sharing)
- [LUT CH4](https://drive.google.com/file/d/196adGp_XCcTXAk3SRjiOnBJxUhDANNvn/view?usp=sharing)
- [EnMAP sample images](https://drive.google.com/drive/folders/1d6Fh7NcXTSF90l_SEm2JfQRTFkgia_Mp?usp=sharing)


---
## Index

1. **Algorithm Theoretical Basis**\
   1.1 Clutter Matched Filter (CMF)\
   1.2 Concentration Estimation\
   1.3 Scene-Specific Target Spectrum Generation\
   1.4 Examples of Automatically Generated Outputs
2. **User Manual for `enmap-ch4-mapper` Docker Container**\
   2.1 Provided Files\
   2.2 Docker Container Usage (single mode)\
   2.3 Example Run Commands\
   2.4 Input Definition\
   2.5 Output Definition\
   2.6 Future Updates
3. **References**


## 1. **Algorithm Theoretical Basis**

### 1.1 Clutter Matched Filter

In the SWIR spectrum, the absorption windows of methane are centered about 1700 nm and 2300 nm. The radiance measured by a hyperspectral sensor is modeled as a superposition of signal $\( b \)$, scaled by its strength $\( \alpha \)$, an average background radiance $\( L_{\text{mean}} \)$ (averaged over the entire image), and a zero-mean noise or clutter term $\( \epsilon \)$ [12][19].

<div align="center">
  
$`L_i = \alpha b + L_{\text{mean}} + \epsilon`$

</div>

$\( \epsilon \)$ represents both sensor noise and scene clutter (non-desirable components). For an uncorrelated background, the optimal filter is the basic matched filter (i.e., the target itself, scaled to make the variance of the filtered image equal to one). Considering the real case of background clutter with correlation between spectral channels, the optimal filter is “matched” both to the signature of the target and the background:

**Clutter Matched Filter (CMF):**

<div align="center">
 
$`q = \frac{C^{-1} b}{\sqrt{b^T C^{-1} b}}`$

</div>

Here, $\( q \)$ is normalized to ensure that in the absence of signal, the variance of the matched filter image, $\( q^T r_i \)$ (for the i-th pixel) is one. Values larger than one indicate strong evidence of the signature's presence, quantified as a "number of sigmas", assuming that the clutter itself is Gaussian. When the clutter's covariance matrix $\( C \)$ is accurately known, the equation defines the optimal matched filter, maximizing the signal-to-clutter ratio. However, this covariance is seldom known beforehand and is typically deduced from the data, often by averaging the outer product of the mean-subtracted radiance across all pixels.

<div align="center">

$`C \approx \frac{1}{N} \sum_{i=1}^N (L_i - L_{\text{mean}})(L_i - L_{\text{mean}})^T`$

</div>

**Cluster Tuned Matched Filter (CTMF):**

The CTMF [12], performs image clustering before applying the matched filter [14][15][16][17][18]. The average background spectrum and covariance matrix are calculated for each class. The CTMF score for the pixel $\((x,y)\)$ in the j-th class is given by:

<div align="center">

$`\alpha_j (x,y) = q_j (L_{(x,y)_j} - L_{\text{mean}_j})`$

</div>

<div align="center">

$`q_j = \frac{b_j^T C_j^{-1}}{\sqrt{b_j^T C_j^{-1} b_j}}`$

</div>

Where the optimal filter $\( q_j \)$ for the j-th class is expressed as [12], $\( L_{\text{mean},j} \)$ is the average radiance of class $j$ and $\( C_j \)$ is the related covariance matrix [18] and $\( b_j \)$ is the target signal. An important assumption is made approximating the off-plume radiance with the average radiance of class $j$, $\( L_{\text{mean},j} \)$, to determine the expression of $\( b \)$.

<div align="center">

$`L_{\text{no\_pl}} = L_{\text{mean},j}`$

</div>

### 1.2 Concentration Estimation (v2)

The methane column enhancement $`\Delta X_{\mathrm{CH}_4}`$ (in ppm·m) is obtained by linearizing the Beer–Lambert law for optically thin plumes ($`\tau \lesssim 0.05`$) and applying a maximum-likelihood matched filter:

<div align="center">

$`\Delta X_{\mathrm{CH}_4}(x,y) =
\frac{(L_{(x,y)} - \mu)^\top\,\Sigma^{-1}\,t}
     {t^\top\,\Sigma^{-1}\,t}`$

</div>

<div align="center">

$`t = -A \bigl(1 + \sec\theta\bigr)\,\mu`$

</div>

where  
* **$`L_{(x,y)}`$** is the at-sensor radiance vector,  
* **$`\mu, \Sigma`$** are the background mean and covariance (global or per-cluster),  
* **$`t`$** is the unit-target spectrum ($`\mathrm{radiance}\cdot(\mathrm{ppm}\,\mathrm{m})^{-1}`$) from LUT/MODTRAN,  
* **$`A`$** is the scene-specific $`\mathrm{CH}_4`$ absorption coefficient,  
* **$`\theta`$** is the solar zenith angle.  

Because $`\Sigma^{-1}`$ appears in both numerator and denominator, the result is already in physical units (ppm·m) without empirical scaling.  

Use `--n_clusters k` to tune $`\mu`$, $`\Sigma`$ and $`t`$ per cluster for improved SNR on heterogeneous scenes.  



### 1.3 Scene-Specific Target Spectrum Automatic Generation

The unit absorption spectrum is derived from multiple simulations with varying methane gas concentrations using radiative transfer models such as MODTRAN6®. This spectrum represents the methane absorption as a function of wavelength, normalized per unit path length and concentration. The unit for this measurement is typically $(ppm·m)\(^{-1}\)$, indicating the inverse of the product of methane concentration (in parts per million) and the path length (in meters) over which the absorption occurs.

Subsequently, the simulated radiance spectra are convolved with the PRISMA spectral response function, and a regression analysis is carried out to obtain the unit absorption spectrum for each PRISMA spectral channel. The slope of the regression line, which best represents the relationship between the concentration-path product and the natural logarithm of the radiance, provides the unit absorption value for each specific wavelength band. This unit absorption spectrum is scaled by element-wise multiplication with the average radiance at each wavelength to generate the target spectrum, which is then used in the matched filter. To automate the generation of the unit target spectrum and make it independent of real-time MODTRAN6® runs, a lookup table (LUT) has been developed based on the methodology described by Foote et al. (2020) [4]. This LUT contains precomputed at-sensor radiances for a wide range of atmospheric and geometric parameters, including variations in sensor altitude, water vapor content, ground elevation, sun zenith angle, and methane concentration. For each PRISMA acquisition, the Level 2C PRISMA image is also used to read the water vapor content, and a Digital Elevation Model (DEM) is used to read the ground elevation. By interpolating within the LUT, it is possible to quickly generate a unit target spectrum that accurately matches the conditions of a given satellite pass.

<div align="center">
<img src="https://github.com/AlFe23/PRISMA-CH4/assets/105355911/160778eb-f03e-477b-83be-0ce0200c0bbb" width="50%">
</div>



### 1.4 Examples of Automatically Generated Outputs

<div align="center">
<img src="https://github.com/user-attachments/assets/89780de4-ebf3-43fd-8c08-378a7bb7c41f" width="50%">
</div>

<div align="center">
<img src="https://github.com/user-attachments/assets/2a324475-4385-49a0-bd2b-1ffc0713c95e" width="50%">
</div>




---

## 2. User Manual for `enmap-ch4-mapper` Docker Container

### 2.1 Provided Files

- `enmap-ch4-mapper.tar` — Docker image
- `run_ctmf_enmap.py` — helper script to load & run the container easily
- `dataset_ch4_full.hdf5` — LUT for unit-absorption spectra

### 2.2 Docker Container Usage

The current image supports **single-mode processing only**. You must supply:

1. VNIR GeoTIFF (`*SPECTRAL_IMAGE_VNIR.TIF`)
2. SWIR GeoTIFF (`*SPECTRAL_IMAGE_SWIR.TIF`)
3. Metadata XML (`*METADATA.XML`)
4. CH4 LUT (`dataset_ch4_full.hdf5`)
5. Output directory

Optional flags:

- `-k <int>` — enable CTMF with *k* clusters (default `1` = global CMF)
- `--min_wl / --max_wl` — restrict retrieval window (nm)

### 2.3 Example Run Commands

#### Using `run_ctmf_enmap.py`

```bash
python3 run_ctmf_enmap.py \
  -t enmap-ch4-mapper.tar \
  /path/to/ENMAP01-…-SPECTRAL_IMAGE_VNIR.TIF \
  /path/to/ENMAP01-…-SPECTRAL_IMAGE_SWIR.TIF \
  /path/to/ENMAP01-…-METADATA.XML \
  /path/to/dataset_ch4_full.hdf5 \
  /path/to/output_dir \
  -k 1
```
---
#### Using plain Docker `enmap-ch4-mapper.tar`

# 1) load image
```
docker load -i enmap-ch4-mapper.tar
```
# 2) run container (single mode)
```
docker run --rm \
  -v /host/data:/data \
  enmap-ch4-mapper:latest \
    "/data/ENMAP01-…-SPECTRAL_IMAGE_VNIR.TIF" \
    "/data/ENMAP01-…-SPECTRAL_IMAGE_SWIR.TIF" \
    "/data/ENMAP01-…-METADATA.XML" \
    "/data/dataset_ch4_full.hdf5" \
    "/data/output" \
    -k 1
```

---

> **Spectral window options**  
> You can control the wavelength range with `--min_wl` and `--max_wl` (in nm).  
> **clustering option**  
> You can choose to activate the CTMF (cluster tuned matched filter) simply setting the clustering flag `-k` >1.  
>  
> **Single mode** requires explicit paths to the extracted `.he5` files.  
> **Batch mode** will scan subfolders of the input directory for PRISMA L1 and L2C files (zipped or unzipped) and process them in sequence.  
>  


### 2.4 Input Definition

| Parameter      | Description                                      |
|----------------|--------------------------------------------------|
| **VNIR_file**  | Path to EnMAP VNIR spectral image (`…_VNIR.TIF`) |
| **SWIR_file**  | Path to EnMAP SWIR spectral image (`…_SWIR.TIF`) |
| **meta_file**  | Path to EnMAP metadata XML                       |
| **lut_file**   | Path to `dataset_ch4_full.hdf5`                  |
| **output_dir** | Directory for results                            |

### 2.5 Output Definition

The container produces GeoTIFF layers mirroring those of the original PRISMA workflow:

- `ENMAP_L1B_CH4_MF.tif` — matched‑filter score  
- `ENMAP_L1B_CH4_concentration.tif` — CH₄ column enhancement (ppm·m)  
- Quick‑look RGB & k‑means classification images  

### 2.6 Future Updates

Column-wise MF computation, will be implemented in an upcoming realease, in order to correct for the smile-effect of EnMAP hyperspectral pushbroom instrument. Batch‑mode processing enabled in an upcoming release without breaking the CLI. 



## 3. References

[1] Foote, M.D., Dennison, P.E., Thorpe, A.K., Thompson, D.R., Jongaramrungruang, S., Frankenberg, C., and Joshi, S.C., 2020. “Fast and accurate retrieval of methane concentration from imaging spectrometer data using sparsity prior.” *IEEE Transactions on Geoscience and Remote Sensing*, 58(9), pp.6480–6492.

[2] Foote, M.D., Dennison, P.E., Sullivan, P.R., O'Neill, K.B., Thorpe, A.K., Thompson, D.R., Cusworth, D.H., Duren, R., and Joshi, S.C., 2021. “Impact of scene-specific enhancement spectra on matched filter greenhouse gas retrievals from imaging spectroscopy.” *Remote Sensing of Environment*, 264, p.112574.

[3] Guanter, L., Irakulis-Loitxate, I., Gorroño, J., Sánchez-García, E., Cusworth, D.H., Varon, D.J., Cogliati, S., and Colombo, R., 2021. “Mapping methane point emissions with the PRISMA spaceborne imaging spectrometer.” *Remote Sensing of Environment*, 265, p.112671.

[4] Roger, J., Irakulis-Loitxate, I., Valverde, A., Gorroño, J., Chabrillat, S., Brell, M., and Guanter, L., 2024. “High-resolution methane mapping with the EnMAP satellite imaging spectroscopy mission.” *IEEE Transactions on Geoscience and Remote Sensing*.

[5] Ferrari, A., Laneve, G., Carvajal Téllez, R.A., Pampanoni, V., Saquella, S., and Guarini, R., 2025. “Analysis of Local Methane Emissions Using Near-Simultaneous Multi-Satellite Observations: Insights from Landfills and Oil-Gas Facilities.” *arXiv preprint* arXiv:2506.01113.

[6] Jervis, D., McKeever, J., Durak, B.O., Sloan, J.J., Gains, D., Varon, D.J., Ramier, A., Strupler, M., and Tarrant, E., 2021. “The GHGSat-D imaging spectrometer.” *Atmospheric Measurement Techniques*, 14(3), pp.2127–2140.

[7] Brodrick, P.G., Thorpe, A.K., Villanueva-Weeks, C.S., Elder, C., Fahlen, J., and Thompson, D.R., 2023. “EMIT Greenhouse Gas Algorithms: Greenhouse Gas Point Source Mapping and Related Products — Theoretical Basis.” JPL Technical Report. Available at: https://lpdaac.usgs.gov/products/emitl2bch4enhv001/

[8] Thompson, D.R. et al., 2024. “On-orbit calibration and performance of the EMIT imaging spectrometer.” *Remote Sensing of Environment*, 303, p.113986.

[9] Zhang, X., Maasakkers, J.D., Roger, J., Guanter, L., Sharma, S., Lama, S., Tol, P., Varon, D.J., Cusworth, D.H., Howell, K., and Thorpe, A., 2024. “Global identification of solid waste methane super emitters using hyperspectral satellites.” *Remote Sensing of Environment* (under review).
