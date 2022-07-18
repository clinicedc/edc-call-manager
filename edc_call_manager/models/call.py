from edc_model.models import BaseUuidModel, HistoricalRecords

from ..model_mixins import CallModelMixin


class Call(CallModelMixin, BaseUuidModel):

    history = HistoricalRecords()

    class Meta(CallModelMixin.Meta):
        verbose_name = "Call"
        verbose_name_plural = "Calls"
