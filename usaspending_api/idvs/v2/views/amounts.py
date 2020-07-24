import logging
import re

from collections import OrderedDict

from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from usaspending_api.awards.models import ParentAward
from usaspending_api.common.cache_decorator import cache_response
from usaspending_api.common.helpers.sql_helpers import execute_sql_to_ordered_dictionary
from usaspending_api.common.validator.award import get_internal_or_generated_award_id_model
from usaspending_api.common.validator.tinyshield import TinyShield
from usaspending_api.awards.v2.data_layer.sql import defc_sql
from usaspending_api.references.models import DisasterEmergencyFundCode

logger = logging.getLogger("console")

child_award_sql = """
    select
        ac.id as award_id
    from
        parent_award pap
        inner join awards ap on ap.id = pap.award_id
        inner join awards ac on ac.fpds_parent_agency_id = ap.fpds_agency_id and ac.parent_award_piid = ap.piid and
            ac.type not like 'IDV%'
    where
        pap.{award_id_column} = '{award_id}'
    """
grandchild_award_sql = """
    select
        ac.id as award_id
    from
        parent_award pap
        inner join parent_award pac on pac.parent_award_id = pap.award_id
        inner join awards ap on ap.id = pac.award_id
        inner join awards ac on ac.fpds_parent_agency_id = ap.fpds_agency_id and ac.parent_award_piid = ap.piid and
            ac.type not like 'IDV%'

    where
        pap.{award_id_column} = '{award_id}'
    """


def fetch_account_details_idv(award_id, award_id_column) -> dict:
    if award_id_column != "award_id":
        award_id = re.sub(r"[']", r"''", award_id)
    children = execute_sql_to_ordered_dictionary(
        child_award_sql.format(award_id=award_id, award_id_column=award_id_column)
    )
    grandchildren = execute_sql_to_ordered_dictionary(
        grandchild_award_sql.format(award_id=award_id, award_id_column=award_id_column)
    )
    covid_defcs = DisasterEmergencyFundCode.objects.filter(group_name="covid_19").values_list("code", flat=True)

    child_award_ids = []
    grandchild_award_ids = []
    child_award_ids.extend([x["award_id"] for x in children])
    grandchild_award_ids.extend([x["award_id"] for x in grandchildren])
    award_id_sql = "faba.award_id in {award_id}".format(award_id="(" + str(child_award_ids).strip("[]") + ")")
    child_results = (
        execute_sql_to_ordered_dictionary(defc_sql.format(award_id_sql=award_id_sql)) if child_award_ids != [] else {}
    )
    award_id_sql = "faba.award_id in {award_id}".format(award_id="(" + str(grandchild_award_ids).strip("[]") + ")")
    grandchild_results = (
        execute_sql_to_ordered_dictionary(defc_sql.format(award_id_sql=award_id_sql))
        if grandchild_award_ids != []
        else {}
    )
    child_outlay_by_code = []
    child_obligation_by_code = []
    child_total_outlay = 0
    child_total_obligations = 0
    for row in child_results:
        if row["disaster_emergency_fund_code"] in covid_defcs:
            child_total_outlay += row["total_outlay"]
            child_total_obligations += row["obligated_amount"]
        child_outlay_by_code.append({"code": row["disaster_emergency_fund_code"], "amount": row["total_outlay"]})
        child_obligation_by_code.append(
            {"code": row["disaster_emergency_fund_code"], "amount": row["obligated_amount"]}
        )
    grandchild_outlay_by_code = []
    grandchild_obligation_by_code = []
    grandchild_total_outlay = 0
    grandchild_total_obligations = 0
    for row in grandchild_results:
        if row["disaster_emergency_fund_code"] in covid_defcs:
            grandchild_total_outlay += row["total_outlay"]
            grandchild_total_obligations += row["obligated_amount"]
        grandchild_outlay_by_code.append({"code": row["disaster_emergency_fund_code"], "amount": row["total_outlay"]})
        grandchild_obligation_by_code.append(
            {"code": row["disaster_emergency_fund_code"], "amount": row["obligated_amount"]}
        )

    results = {
        "child_total_account_outlay": child_total_outlay,
        "child_total_account_obligation": child_total_obligations,
        "child_account_outlays_by_defc": child_outlay_by_code,
        "child_account_obligations_by_defc": child_obligation_by_code,
        "grandchild_total_account_outlay": grandchild_total_outlay,
        "grandchild_total_account_obligation": grandchild_total_obligations,
        "grandchild_account_outlays_by_defc": grandchild_outlay_by_code,
        "grandchild_account_obligations_by_defc": grandchild_obligation_by_code,
    }
    return results


class IDVAmountsViewSet(APIView):
    """
    Returns counts and dollar figures for a specific IDV.
    """

    endpoint_doc = "usaspending_api/api_contracts/contracts/v2/idvs/amounts/award_id.md"

    throttle_scope = "idvs_amount"

    @staticmethod
    def _parse_and_validate_request(requested_award: str) -> dict:
        return TinyShield([get_internal_or_generated_award_id_model()]).block({"award_id": requested_award})

    @staticmethod
    def _business_logic(request_data: dict) -> OrderedDict:
        # By this point, our award_id has been validated and cleaned up by
        # TinyShield.  We will either have an internal award id that is an
        # integer or a generated award id that is a string.
        award_id = request_data["award_id"]
        award_id_column = "award_id" if type(award_id) is int else "generated_unique_award_id"

        try:
            parent_award = ParentAward.objects.get(**{award_id_column: award_id})
            account_data = fetch_account_details_idv(award_id, award_id_column)
            return OrderedDict(
                (
                    ("award_id", parent_award.award_id),
                    ("generated_unique_award_id", parent_award.generated_unique_award_id),
                    ("child_idv_count", parent_award.direct_idv_count),
                    ("child_award_count", parent_award.direct_contract_count),
                    ("child_award_total_obligation", parent_award.direct_total_obligation),
                    ("child_award_base_and_all_options_value", parent_award.direct_base_and_all_options_value),
                    ("child_award_base_exercised_options_val", parent_award.direct_base_exercised_options_val),
                    ("child_total_account_outlay", account_data["child_total_account_outlay"]),
                    ("child_total_account_obligation", account_data["child_total_account_obligation"]),
                    ("child_account_outlays_by_defc", account_data["child_account_outlays_by_defc"]),
                    ("child_account_obligations_by_defc", account_data["child_account_obligations_by_defc"]),
                    ("grandchild_award_count", parent_award.rollup_contract_count - parent_award.direct_contract_count),
                    (
                        "grandchild_award_total_obligation",
                        parent_award.rollup_total_obligation - parent_award.direct_total_obligation,
                    ),
                    (
                        "grandchild_award_base_and_all_options_value",
                        parent_award.rollup_base_and_all_options_value - parent_award.direct_base_and_all_options_value,
                    ),
                    (
                        "grandchild_award_base_exercised_options_val",
                        parent_award.rollup_base_exercised_options_val - parent_award.direct_base_exercised_options_val,
                    ),
                    ("grandchild_total_account_outlay", account_data["grandchild_total_account_outlay"]),
                    ("grandchild_total_account_obligation", account_data["grandchild_total_account_obligation"]),
                    ("grandchild_account_outlays_by_defc", account_data["grandchild_account_outlays_by_defc"]),
                    ("grandchild_account_obligations_by_defc", account_data["grandchild_account_obligations_by_defc"]),
                )
            )
        except ParentAward.DoesNotExist:
            logger.info("No IDV Award found where '%s' is '%s'" % next(iter(request_data.items())))
            raise NotFound("No IDV award found with this id")

    @cache_response()
    def get(self, request: Request, requested_award: str) -> Response:
        request_data = self._parse_and_validate_request(requested_award)
        return Response(self._business_logic(request_data))
