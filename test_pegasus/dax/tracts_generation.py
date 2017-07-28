from Pegasus.DAX3 import File, Job, Link
from mappings import TractsGenFiles, TractsGenJobNames, CoregFiles, DWIFiles


class TractsGeneration(object):
    def __init__(self, dwi_multi_shell=False, mrtrix_threads="2"):
        self.dwi_multi_shell = dwi_multi_shell
        self.mrtrix_threads = mrtrix_threads

    # job_t1_in_d = job12, job_mask = job5, job_aparc_aseg_in_d = job21
    def add_tracts_generation_steps(self, dax, job_t1_in_d, job_mask, job_aparc_aseg_in_d):
        t1_in_d = File(CoregFiles.T1_IN_D.value)
        file_5tt = File(TractsGenFiles.FILE_5TT_MIF.value)
        job1 = Job(TractsGenJobNames.JOB_5TTGEN.value, node_label="Generate 5tt MIF")
        job1.addArguments(t1_in_d, file_5tt)
        job1.uses(t1_in_d, link=Link.INPUT)
        job1.uses(file_5tt, link=Link.OUTPUT, transfer=True, register=False)
        dax.addJob(job1)

        dax.depends(job1, job_t1_in_d)

        file_gmwmi = File(TractsGenFiles.GMWMI_MIF.value)
        job2 = Job(TractsGenJobNames.JOB_5TT2GMWMI.value, node_label="Extract GMWMI")
        job2.addArguments(file_5tt, file_gmwmi, "-nthreads", self.mrtrix_threads)
        job2.uses(file_5tt, link=Link.INPUT)
        job2.uses(file_gmwmi, link=Link.OUTPUT, transfer=True, register=False)
        dax.addJob(job2)

        dax.depends(job2, job1)

        file_5ttvis = File(TractsGenFiles.FILE_5TTVIS_MIF.value)
        job3 = Job(TractsGenJobNames.JOB_5TT2VIS.value, node_label="Generate TT2VIS MIF")
        job3.addArguments(file_5tt, file_5ttvis)
        job3.uses(file_5tt, link=Link.INPUT)
        job3.uses(file_5ttvis, link=Link.OUTPUT, transfer=True, register=False)
        dax.addJob(job3)

        dax.depends(job3, job2)

        file_wm_fod = None
        last_job = None

        dwi_mif = File(DWIFiles.DWI_MIF.value)
        mask_mif = File(DWIFiles.MASK_MIF.value)

        if self.dwi_multi_shell is True:
            file_RF_WM = File(TractsGenFiles.RF_WM.value)
            file_RF_GM = File(TractsGenFiles.RF_GM.value)
            file_RF_CSF = File(TractsGenFiles.RF_CSF.value)
            file_RF_voxels = File(TractsGenFiles.RF_VOXELS.value)
            job4 = Job(TractsGenJobNames.DWI2RESPONSE_MSMT.value)
            job4.addArguments(dwi_mif, file_5tt, file_RF_WM, file_RF_GM, file_RF_CSF,
                              file_RF_voxels, self.mrtrix_threads)
            job4.uses(dwi_mif, link=Link.INPUT)
            job4.uses(file_5tt, link=Link.INPUT)
            job4.uses(file_RF_WM, link=Link.OUTPUT, transfer=True, register=False)
            job4.uses(file_RF_GM, link=Link.OUTPUT, transfer=True, register=False)
            job4.uses(file_RF_CSF, link=Link.OUTPUT, transfer=True, register=False)
            job4.uses(file_RF_voxels, link=Link.OUTPUT, transfer=True, register=False)
            dax.addJob(job4)

            dax.depends(job4, job3)

            gm_mif = File(DWIFiles.GM_MIF.value)
            csf_mif = File(DWIFiles.CSF_MIF.value)
            file_wm_fod = File(TractsGenFiles.WM_FOD_MIF.value)
            job5 = Job(TractsGenJobNames.MSDWI2FOD.value)
            job5.addArguments("msmt_csd", dwi_mif, file_RF_WM, file_wm_fod, file_RF_GM, gm_mif, file_RF_CSF, csf_mif,
                              "-mask", mask_mif, "-nthreads", self.mrtrix_threads)
            job5.uses(dwi_mif, link=Link.INPUT)
            job5.uses(file_RF_WM, link=Link.INPUT)
            job5.uses(file_RF_GM, link=Link.INPUT)
            job5.uses(file_RF_CSF, link=Link.INPUT)
            job5.uses(mask_mif, link=Link.INPUT)
            job5.uses(file_wm_fod, link=Link.OUTPUT, transfer=True, register=False)
            job5.uses(gm_mif, link=Link.OUTPUT, transfer=True, register=False)
            job5.uses(csf_mif, link=Link.OUTPUT, transfer=True, register=False)
            dax.addJob(job5)

            dax.depends(job5, job4)

            last_job = job5

        else:
            file_respone = File(TractsGenFiles.RESPONSE_TXT.value)
            job4 = Job(TractsGenJobNames.DWI2RESPONSE.value, node_label="Compute the DWI Response")
            job4.addArguments(dwi_mif, file_respone, mask_mif)
            job4.uses(dwi_mif, link=Link.INPUT)
            job4.uses(mask_mif, link=Link.INPUT)
            job4.uses(file_respone, link=Link.OUTPUT, transfer=True, register=False)
            dax.addJob(job4)

            dax.depends(job4, job_mask)

            file_wm_fod = File(TractsGenFiles.WM_FOD_MIF.value)
            job5 = Job(TractsGenJobNames.DWI2FOD.value, node_label="Obtain WM FOD")
            job5.addArguments("csd", dwi_mif, file_respone, file_wm_fod, "-mask", mask_mif,
                              "-nthreads",
                              self.mrtrix_threads)
            job5.uses(dwi_mif, link=Link.INPUT)
            job5.uses(file_respone, link=Link.INPUT)
            job5.uses(mask_mif, link=Link.INPUT)
            job5.uses(file_wm_fod, link=Link.OUTPUT, transfer=True, register=False)
            dax.addJob(job5)

            dax.depends(job5, job4)

            last_job = job5

        file_strmlns = File(TractsGenFiles.FILE_25M_TCK.value)
        job6 = Job(TractsGenJobNames.TCKGEN.value, node_label="Generate tracts")
        job6.addArguments(file_wm_fod, file_strmlns, "-number", "25M", "-seed_gmwmi", file_gmwmi, "-act", file_5tt,
                          "-unidirectional", "-maxlength", "250", "-step", "0.5", "-nthreads", self.mrtrix_threads)
        job6.uses(file_wm_fod, link=Link.INPUT)
        job6.uses(file_gmwmi, link=Link.INPUT)
        job6.uses(file_5tt, link=Link.INPUT)
        job6.uses(file_strmlns, link=Link.OUTPUT, transfer=True, register=False)
        dax.addJob(job6)

        dax.depends(job6, last_job)
        dax.depends(job6, job1)

        file_strmlns_sift = File(TractsGenFiles.FILE_5M_TCK.value)
        job7 = Job(TractsGenJobNames.TCKSIFT.value, node_label="Tracts SIFT")
        job7.addArguments(file_strmlns, file_wm_fod, file_strmlns_sift, "-term_number", "5M", "-act", file_5tt,
                          "-nthreads", self.mrtrix_threads)
        job7.uses(file_strmlns, link=Link.INPUT)
        job7.uses(file_wm_fod, link=Link.INPUT)
        job7.uses(file_5tt, link=Link.INPUT)
        job7.uses(file_strmlns_sift, link=Link.OUTPUT, transfer=True, register=False)
        dax.addJob(job7)

        dax.depends(job7, job6)
        dax.depends(job7, job1)

        b0_nii_gz = File(DWIFiles.B0_NII_GZ.value)
        file_tdi_ends = File(TractsGenFiles.TDI_ENDS_MIF.value)
        job8 = Job(TractsGenJobNames.TCKMAP.value, node_label="TCKMAP")
        job8.addArguments(file_strmlns_sift, file_tdi_ends, "-vox", "1", "-template", b0_nii_gz)
        job8.uses(file_strmlns_sift, link=Link.INPUT)
        job8.uses(b0_nii_gz, link=Link.INPUT)
        job8.uses(file_tdi_ends, link=Link.OUTPUT, transfer=True, register=False)
        dax.addJob(job8)

        dax.depends(job8, job7)

        aparc_aseg_in_d = File(CoregFiles.APARC_AGEG_IN_D.value)
        file_vol_lbl = File("aparc_aseg_lbl.nii.gz")
        fs_color_lut = File("fs_color_lut.txt")
        fs_default = File("fs_default.txt")
        job9 = Job(TractsGenJobNames.LABEL_CONVERT.value, node_label="Compute APARC+ASEG labeled for tracts")
        job9.addArguments(aparc_aseg_in_d, fs_color_lut, fs_default, file_vol_lbl)
        job9.uses(aparc_aseg_in_d, link=Link.INPUT)
        job9.uses(fs_color_lut, link=Link.INPUT)
        job9.uses(fs_default, link=Link.INPUT)
        job9.uses(file_vol_lbl, link=Link.OUTPUT, transfer=True, register=False)
        dax.addJob(job9)

        dax.depends(job9, job_aparc_aseg_in_d)

        file_aparc_aseg_counts5M_csv = File("aparc+aseg_counts5M.csv")
        job10 = Job(TractsGenJobNames.TCK2CONNECTOME.value, node_label="Generate weigths")
        job10.addArguments(file_strmlns_sift, file_vol_lbl, "-assignment_radial_search", "2",
                           file_aparc_aseg_counts5M_csv)
        job10.uses(file_strmlns_sift, link=Link.INPUT)
        job10.uses(file_vol_lbl, link=Link.INPUT)
        job10.uses(file_aparc_aseg_counts5M_csv, link=Link.OUTPUT, transfer=True, register=False)
        dax.addJob(job10)

        dax.depends(job10, job7)
        dax.depends(job10, job9)

        file_aparc_aseg_mean_tract_lengths5M_csv = File("aparc+aseg_mean_tract_lengths5M.csv")
        job11 = Job(TractsGenJobNames.TCK2CONNECTOME.value, node_label="Generate tract lengths")
        job11.addArguments(file_strmlns_sift, file_vol_lbl, "-assignment_radial_search", "2", "-scale_length",
                           "-stat_edge", "mean", file_aparc_aseg_mean_tract_lengths5M_csv)
        job11.uses(file_strmlns_sift, link=Link.INPUT)
        job11.uses(file_vol_lbl, link=Link.INPUT)
        job11.uses(file_aparc_aseg_mean_tract_lengths5M_csv, link=Link.OUTPUT, transfer=True, register=False)
        dax.addJob(job11)

        dax.depends(job11, job7)
        dax.depends(job11, job9)
