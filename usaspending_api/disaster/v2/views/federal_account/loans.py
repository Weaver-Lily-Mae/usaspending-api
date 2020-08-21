from django.db.models import F, Count, Sum
from rest_framework.response import Response
from usaspending_api.accounts.models import TreasuryAppropriationAccount
from usaspending_api.common.cache_decorator import cache_response
from usaspending_api.disaster.v2.views.disaster_base import (
    DisasterBase,
    LoansPaginationMixin,
    LoansMixin,
    FabaOutlayMixin,
)
from usaspending_api.disaster.v2.views.federal_account.spending import construct_response


class LoansViewSet(LoansMixin, LoansPaginationMixin, FabaOutlayMixin, DisasterBase):
    """ Returns loan disaster spending by federal account. """

    endpoint_doc = "usaspending_api/api_contracts/contracts/v2/disaster/federal_account/loans.md"

    @cache_response()
    def post(self, request):
        # rename hack to use the Dataclasses, setting to Dataclass attribute name
        if self.pagination.sort_key == "face_value_of_loan":
            self.pagination.sort_key = "total_budgetary_resources"

        results = construct_response(self.queryset, self.pagination)

        # rename hack to use the Dataclasses, swapping back in desired loan field name
        for result in results["results"]:
            for child in result["children"]:
                child["face_value_of_loan"] = child.pop("total_budgetary_resources")
            result["face_value_of_loan"] = result.pop("total_budgetary_resources")

        return Response(results)

    @property
    def queryset(self):
        query = self.construct_loan_queryset(
            "treasury_account__treasury_account_identifier", TreasuryAppropriationAccount, "treasury_account_identifier"
        )

        annotations = {
            "fa_code": F("federal_account__federal_account_code"),
            "award_count": query.award_count_column,
            "description": F("account_title"),
            "code": F("tas_rendering_label"),
            "id": F("treasury_account_identifier"),
            "fa_description": F("federal_account__account_title"),
            "fa_id": F("federal_account_id"),
            "obligation": query.obligation_column,
            "outlay": query.outlay_column,
            # hack to use the Dataclasses, will be renamed later
            "total_budgetary_resources": query.face_value_of_loan_column,
        }

        aggregations = {
            "award_count": Count("id"),
            "obligation_sum": Sum("obligation"),
            "outlay_sum": Sum("outlay"),
        }

        return {
            "totals": query.queryset.annotate(**annotations).aggregate(**aggregations),
            "results": query.queryset.annotate(**annotations).values(*annotations),
        }
