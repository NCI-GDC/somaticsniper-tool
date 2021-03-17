#!/usr/bin/env python3

import unittest
from types import SimpleNamespace
from unittest import mock

from somaticsniper_tool import multi_somaticsniper as MOD


class ThisTestCase(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.mocks = SimpleNamespace(
            futures=mock.MagicMock(spec_set=MOD.concurrent.futures),
            open=mock.MagicMock(spec_set=open),
            SOMATICSNIPER=mock.MagicMock(spec_set=MOD.SomaticSniper),
            UTILS=mock.MagicMock(spec_set=MOD.utils),
            SAMTOOLS=mock.MagicMock(spec_set=MOD.SamtoolsView),
            HIGHCONFIDENCE=mock.MagicMock(spec_set=MOD.HighConfidence),
            ANNOTATE=mock.MagicMock(spec_set=MOD.Annotate),
            SNPFILTER=mock.MagicMock(spec_set=MOD.SnpFilter),
        )

    def tearDown(self):
        super().tearDown()


class Test_process_argv(ThisTestCase):
    def setUp(self):
        super().setUp()
        self.required_args = (
            (("--thread-count", "2"), ('thread_count', 2)),
            (("--mpileup", "foo"), ('mpileup', ["foo"])),
            (
                ("--reference-path", "/path/to/reference"),
                ('reference_path', "/path/to/reference",),
            ),
            (("--tumor-bam", "tumor.bam"), ('tumor_bam', "tumor.bam")),
            (("--normal-bam", "normal.bam"), ('normal_bam', "normal.bam")),
        )
        self.args_list = []
        for tup in self.required_args:
            self.args_list.extend(tup[0])

    def test_required_args_processed(self):
        found = MOD.process_argv(self.args_list)
        for _, (k, v) in self.required_args:
            with self.subTest(k=k):
                self.assertEqual(getattr(found, k), v)

    def test_multiple_mpileup_appended(self):
        extra_mpileups = ("bar.mpileup", "baz.mpileup")
        for m in extra_mpileups:
            self.args_list.extend(['--mpileup', m])
        print(self.args_list)
        found = MOD.process_argv(self.args_list)
        mpileups = found.mpileup
        for m in extra_mpileups:
            with self.subTest(m=m):
                self.assertTrue(m in mpileups)


class Test_tpe_submit_commands(ThisTestCase):
    def setUp(self):
        super().setUp()
        self.args = dict(
            normal_bam="/foo/bar/normal.bam",
            tumor_bam="/foo/bar/tumor.bam",
            snpfilter="snp_filter.pl",
            highconfidence="highconfidence.pl",
            mpileup=["chr1-2-3.mpileup", "chr4-5-6.mpileup"],
            thread_count=42,
        )
        self.run_args = SimpleNamespace(**self.args)

    def tearDown(self):
        super().tearDown()

    def test_threadpool_executor_init_with_expected_args(self):
        mock_fn = mock.Mock()
        found = MOD.tpe_submit_commands(self.run_args, fn=mock_fn, _di=self.mocks)
        self.mocks.futures.ThreadPoolExecutor.assert_called_once_with(
            max_workers=self.run_args.thread_count
        )

    def test_executor_called_with_expected_args(self):
        mock_fn = mock.Mock()
        mock_executor = mock.MagicMock(
            spec_set=MOD.concurrent.futures.ThreadPoolExecutor
        )
        self.mocks.futures.ThreadPoolExecutor.return_value.__enter__.return_value = (
            mock_executor
        )
        found = MOD.tpe_submit_commands(self.run_args, fn=mock_fn, _di=self.mocks)
        mock_executor.submit.assert_has_calls(
            [
                mock.call(
                    mock_fn,
                    region,
                    normal_bam=self.run_args.normal_bam,
                    tumor_bam=self.run_args.tumor_bam,
                    snpfilter=self.run_args.snpfilter,
                    high_confidence=self.run_args.highconfidence,
                )
                for region in self.run_args.mpileup
            ],
            any_order=True,
        )


class Test_Multithread_Somaticsniper(ThisTestCase):
    def setUp(self):
        super().setUp()

        self.args = dict(
            normal_bam="/foo/bar/normal.bam",
            tumor_bam="/foo/bar/tumor.bam",
            snpfilter="snp_filter.pl",
            high_confidence="highconfidence.pl",
        )
        self.mpileup = "chr1-2-3.mpileup"

    def tearDown(self):
        super().tearDown()

    def test_all(self):
        found = MOD.multithread_somaticsniper(
            self.mpileup,
            **self.args,
            _annotate=self.mocks.ANNOTATE,
            _highconfidence=self.mocks.HIGHCONFIDENCE,
            _samtools=self.mocks.SAMTOOLS,
            _somaticsniper=self.mocks.SOMATICSNIPER,
            _snpfilter=self.mocks.SNPFILTER,
        )

    def test_somaticsniper_called_with_expected_region_arg(self):
        found = MOD.multithread_somaticsniper(
            self.mpileup,
            **self.args,
            _annotate=self.mocks.ANNOTATE,
            _highconfidence=self.mocks.HIGHCONFIDENCE,
            _samtools=self.mocks.SAMTOOLS,
            _somaticsniper=self.mocks.SOMATICSNIPER,
            _snpfilter=self.mocks.SNPFILTER,
        )

        self.mocks.SOMATICSNIPER.assert_called_once_with("chr1-2-3")

    def test_samtools_views_called_with_expected_bams(self):

        mock_somatic_sniper = mock.MagicMock(spec_set=MOD.SomaticSniper)
        self.mocks.SOMATICSNIPER.return_value = mock_somatic_sniper

        region = "chr1:2-3"
        basename = "chr1-2-3"
        self.mocks.UTILS.get_region_from_name.return_value = region, basename

        found = MOD.multithread_somaticsniper(
            self.mpileup,
            **self.args,
            _annotate=self.mocks.ANNOTATE,
            _highconfidence=self.mocks.HIGHCONFIDENCE,
            _samtools=self.mocks.SAMTOOLS,
            _somaticsniper=self.mocks.SOMATICSNIPER,
            _snpfilter=self.mocks.SNPFILTER,
            _utils=self.mocks.UTILS,
        )
        expected_calls = [
            mock.call(self.args["normal_bam"], region),
            mock.call(self.args["tumor_bam"], region),
        ]
        self.mocks.SAMTOOLS.assert_has_calls(expected_calls, any_order=True)

    def test_somaticsniper_run_called_with_samtools_views(self):
        normal_bam_path = "normal.bam"
        tumor_bam_path = "tumor.bam"

        mock_normal_samtools = mock.MagicMock(spec_set=MOD.SamtoolsView)
        mock_normal_samtools.__enter__.return_value = normal_bam_path

        mock_tumor_samtools = mock.MagicMock(spec_set=MOD.SamtoolsView)
        mock_tumor_samtools.__enter__.return_value = tumor_bam_path

        self.mocks.SAMTOOLS.side_effect = [mock_normal_samtools, mock_tumor_samtools]

        mock_somatic_sniper = mock.MagicMock(spec_set=MOD.SomaticSniper)
        self.mocks.SOMATICSNIPER.return_value = mock_somatic_sniper

        found = MOD.multithread_somaticsniper(
            self.mpileup,
            **self.args,
            _annotate=self.mocks.ANNOTATE,
            _highconfidence=self.mocks.HIGHCONFIDENCE,
            _samtools=self.mocks.SAMTOOLS,
            _somaticsniper=self.mocks.SOMATICSNIPER,
            _snpfilter=self.mocks.SNPFILTER,
        )
        mock_somatic_sniper.run.assert_called_once_with(
            normal_bam=normal_bam_path, tumor_bam=tumor_bam_path,
        )

    def test_snpfilter_called_with_expected_args(self):

        out_vcf = "somatic_sniper.vcf"
        self.mocks.SOMATICSNIPER.return_value.run.return_value = out_vcf

        mock_snpfilter = mock.MagicMock(spec_set=MOD.SnpFilter)
        self.mocks.SNPFILTER.return_value = mock_snpfilter

        found = MOD.multithread_somaticsniper(
            self.mpileup,
            **self.args,
            _annotate=self.mocks.ANNOTATE,
            _highconfidence=self.mocks.HIGHCONFIDENCE,
            _samtools=self.mocks.SAMTOOLS,
            _somaticsniper=self.mocks.SOMATICSNIPER,
            _snpfilter=self.mocks.SNPFILTER,
        )

        self.mocks.SNPFILTER.assert_called_once_with(
            self.args["snpfilter"], out_vcf, self.mpileup
        )
        mock_snpfilter.run.assert_called_once_with()

    def test_highconfidence_called_with_expected_args(self):

        out_vcf = "somatic_sniper.vcf"
        snpfilter_out = "{}.SNPfilter".format(out_vcf)
        self.mocks.SOMATICSNIPER.return_value.run.return_value = out_vcf

        mock_high_confidence = mock.MagicMock(spec_set=MOD.HighConfidence)
        self.mocks.HIGHCONFIDENCE.return_value = mock_high_confidence

        found = MOD.multithread_somaticsniper(
            self.mpileup,
            **self.args,
            _annotate=self.mocks.ANNOTATE,
            _highconfidence=self.mocks.HIGHCONFIDENCE,
            _samtools=self.mocks.SAMTOOLS,
            _somaticsniper=self.mocks.SOMATICSNIPER,
            _snpfilter=self.mocks.SNPFILTER,
        )
        self.mocks.HIGHCONFIDENCE.assert_called_once_with(
            self.args["high_confidence"], snpfilter_out
        )
        mock_high_confidence.run.assert_called_once_with()

    def test_annotate_context_called_with_expected_args(self):
        region = "foo:bar"
        basename = "foo-bar"
        self.mocks.UTILS.get_region_from_name.return_value = region, basename

        out_vcf = "somatic_sniper.vcf"
        snpfilter_out = "{}.SNPfilter".format(out_vcf)
        high_confidence_out = "{}.hc".format(snpfilter_out)

        annotated_file = "{}.annotated.vcf".format(basename)

        self.mocks.SOMATICSNIPER.return_value.run.return_value = out_vcf

        found = MOD.multithread_somaticsniper(
            self.mpileup,
            **self.args,
            _annotate=self.mocks.ANNOTATE,
            _highconfidence=self.mocks.HIGHCONFIDENCE,
            _samtools=self.mocks.SAMTOOLS,
            _somaticsniper=self.mocks.SOMATICSNIPER,
            _snpfilter=self.mocks.SNPFILTER,
            _utils=self.mocks.UTILS,
        )
        self.mocks.ANNOTATE.assert_called_once_with(annotated_file)

    def test_annotate_instance_called_with_expected_args(self):
        region = "foo:bar"
        basename = "foo-bar"
        self.mocks.UTILS.get_region_from_name.return_value = region, basename

        out_vcf = "somatic_sniper.vcf"
        snpfilter_out = "{}.SNPfilter".format(out_vcf)
        high_confidence_out = "{}.hc".format(snpfilter_out)

        annotated_file = "{}.annotated.vcf".format(basename)
        self.mocks.SOMATICSNIPER.return_value.run.return_value = out_vcf

        mock_annotate = mock.MagicMock(spec_set=MOD.Annotate)
        self.mocks.ANNOTATE.return_value.__enter__.return_value = mock_annotate

        found = MOD.multithread_somaticsniper(
            self.mpileup,
            **self.args,
            _annotate=self.mocks.ANNOTATE,
            _highconfidence=self.mocks.HIGHCONFIDENCE,
            _samtools=self.mocks.SAMTOOLS,
            _somaticsniper=self.mocks.SOMATICSNIPER,
            _snpfilter=self.mocks.SNPFILTER,
            _utils=self.mocks.UTILS,
        )
        mock_annotate.assert_called_once_with(out_vcf, high_confidence_out)


# __END__
