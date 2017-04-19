import geobuf
from rest_framework.renderers import BaseRenderer


class GeobufRenderer(BaseRenderer):
    """Renderer for downloading geobuf versions of GeoJSON files.

    See https://github.com/mapbox/geobuf
    """

    media_type = 'application/octet-stream'
    format = 'pbf'
    charset = None
    render_style = 'binary'

    def render(self, data,
               media_type=None, renderer_context=None, format=None):
        return geobuf.encode(data)
