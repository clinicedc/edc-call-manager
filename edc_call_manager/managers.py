from django.contrib.admin.models import LogEntryManager
from django.db import models


class CallManager(models.Manager):
    def get_by_natural_key(self, subject_identifier, label, scheduled):
        return self.get(
            subject_identifier=subject_identifier, label=label, scheduled=scheduled
        )


class LogManager(models.Manager):
    def get_by_natural_key(self, log_datetime, subject_identifier, label, scheduled):
        return self.get(
            log_datetime=log_datetime,
            call__subject_identifier=subject_identifier,
            call__label=label,
            call__scheduled=scheduled,
        )


class LogEntryManager(LogEntryManager):
    def get_by_natural_key(
        self, call_datetime, log_datetime, subject_identifier, label, scheduled
    ):
        return self.get(
            call_datetime=call_datetime,
            log__log_datetime=log_datetime,
            log__call__subject_identifier=subject_identifier,
            log__call__label=label,
            log__call__scheduled=scheduled,
        )
