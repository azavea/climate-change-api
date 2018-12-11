import boto3


BUCKET = 'nasanex'


class NetCdfDownloader(object):
    """Generic class for downloading a NetCDF object from S3 to a target path."""

    def get_object_key_format(self):
        raise NotImplementedError()

    def get_model_ensemble(self, model, rcp):
        raise NotImplementedError()

    def get_object_key(self, model, rcp, year, var):
        ensemble = self.get_model_ensemble(model, rcp)
        key_format = self.get_object_key_format()
        return key_format.format(
            rcp=rcp.lower(),
            model=model,
            year=year,
            var=var,
            ensemble=ensemble
        )

    def download(self, logger, rcp, model, year, var, filename):
        key = self.get_object_key(model, rcp, year, var)

        s3 = boto3.resource('s3')
        logger.warning('Downloading file: s3://{}/{}'.format(BUCKET, key))
        s3.meta.client.download_file(BUCKET, key, filename)


class GddpNetCdfDownloader(NetCdfDownloader):
    """Specialized NetCdfDownloader for downloading GDDP-originated S3 objects from S3."""

    def get_object_key_format(self):
        return ('NEX-GDDP/BCSD/{rcp}/day/atmos/{var}/{ensemble}/v1.0/'
                '{var}_day_BCSD_{rcp}_{ensemble}_{model}_{year}.nc')

    def get_model_ensemble(self, model, rcp):
        return 'r1i1p1'


class LocaNetCdfDownloader(NetCdfDownloader):
    """Specialized NetCdfDownloader for downloading LOCA-originated S3 objects from S3."""

    def get_object_key_format(self):
        return ('LOCA/{model}/16th/{rcp}/{ensemble}/{var}/'
                '{var}_day_{model}_{rcp}_{ensemble}_{year}0101-{year}1231.LOCA_2016-04-02.16th.nc')

    def get_model_ensemble(self, model, rcp):
        """Return ensemble given LOCA model and scenario."""
        ensembles = {
            'historical': {
                'CCSM4': 'r6i1p1',
                'GISS-E2-H': 'r6i1p1',
                'GISS-E2-R': 'r6i1p1',
            },
            'RCP45': {
                'CCSM4': 'r6i1p1',
                'EC-EARTH': 'r8i1p1',
                'GISS-E2-H': 'r6i1p3',
                'GISS-E2-R': 'r6i1p1'
            },
            'RCP85': {
                'CCSM4': 'r6i1p1',
                'EC-EARTH': 'r2i1p1',
                'GISS-E2-H': 'r2i1p1',
                'GISS-E2-R': 'r2i1p1'
            }
        }
        try:
            return ensembles[rcp][model]
        except KeyError:
            return 'r1i1p1'


def get_netcdf_downloader(dataset):
    downloader_class = {
        'LOCA': LocaNetCdfDownloader,
        'NEX-GDDP': GddpNetCdfDownloader
    }[dataset]
    return downloader_class()
