import pytest

from model_mommy import mommy

from usaspending_api.references.models import DisasterEmergencyFundCode
from usaspending_api.submissions.models import SubmissionAttributes
from usaspending_api.disaster.tests.fixtures.award_count_data import _normal_award


@pytest.fixture
def basic_faba_with_object_class(award_count_sub_schedule, award_count_submission, defc_codes):
    basic_object_class = _major_object_class_with_children("001", [1])

    award = _normal_award()

    mommy.make(
        "awards.FinancialAccountsByAwards",
        parent_award_id="basic award",
        award=award,
        disaster_emergency_fund=DisasterEmergencyFundCode.objects.filter(code="M").first(),
        submission=SubmissionAttributes.objects.all().first(),
        object_class=basic_object_class[0],
    )


@pytest.fixture
def basic_fa_by_object_class_with_object_class(award_count_sub_schedule, award_count_submission, defc_codes):
    basic_object_class = _major_object_class_with_children("001", [1])

    mommy.make(
        "financial_activities.FinancialAccountsByProgramActivityObjectClass",
        disaster_emergency_fund=DisasterEmergencyFundCode.objects.filter(code="M").first(),
        submission=SubmissionAttributes.objects.all().first(),
        object_class=basic_object_class[0],
        obligations_incurred_by_program_object_class_cpe=9,
        gross_outlay_amount_by_program_object_class_cpe=0,
    )


@pytest.fixture
def basic_fa_by_object_class_with_multpile_object_class(
    award_count_sub_schedule, award_count_quarterly_submission, defc_codes
):
    major_object_class_1 = _major_object_class_with_children("001", [1, 2, 3])

    mommy.make(
        "financial_activities.FinancialAccountsByProgramActivityObjectClass",
        disaster_emergency_fund=DisasterEmergencyFundCode.objects.filter(code="M").first(),
        submission=SubmissionAttributes.objects.all().first(),
        object_class=major_object_class_1[0],
        obligations_incurred_by_program_object_class_cpe=10,
        gross_outlay_amount_by_program_object_class_cpe=2,
    )

    mommy.make(
        "financial_activities.FinancialAccountsByProgramActivityObjectClass",
        disaster_emergency_fund=DisasterEmergencyFundCode.objects.filter(code="M").first(),
        submission=SubmissionAttributes.objects.all().first(),
        object_class=major_object_class_1[1],
        obligations_incurred_by_program_object_class_cpe=0,
        gross_outlay_amount_by_program_object_class_cpe=20,
    )

    mommy.make(
        "financial_activities.FinancialAccountsByProgramActivityObjectClass",
        disaster_emergency_fund=DisasterEmergencyFundCode.objects.filter(code="M").first(),
        submission=SubmissionAttributes.objects.all().first(),
        object_class=major_object_class_1[2],
        obligations_incurred_by_program_object_class_cpe=1,
        gross_outlay_amount_by_program_object_class_cpe=0,
    )


@pytest.fixture
def basic_fa_by_object_class_with_multpile_object_class_of_same_code(
    award_count_sub_schedule, award_count_quarterly_submission, defc_codes
):
    class1 = mommy.make(
        "references.ObjectClass",
        id=9,
        major_object_class="major",
        major_object_class_name=f"major name",
        object_class=f"0001",
        object_class_name=f"0001 name",
    )

    class2 = mommy.make(
        "references.ObjectClass",
        id=10,
        major_object_class="major",
        major_object_class_name=f"major name",
        object_class=f"0001",
        object_class_name=f"0001 name",
    )

    mommy.make(
        "financial_activities.FinancialAccountsByProgramActivityObjectClass",
        disaster_emergency_fund=DisasterEmergencyFundCode.objects.filter(code="M").first(),
        submission=SubmissionAttributes.objects.all().first(),
        object_class=class1,
        obligations_incurred_by_program_object_class_cpe=10,
        gross_outlay_amount_by_program_object_class_cpe=2,
    )

    mommy.make(
        "financial_activities.FinancialAccountsByProgramActivityObjectClass",
        disaster_emergency_fund=DisasterEmergencyFundCode.objects.filter(code="M").first(),
        submission=SubmissionAttributes.objects.all().first(),
        object_class=class2,
        obligations_incurred_by_program_object_class_cpe=0,
        gross_outlay_amount_by_program_object_class_cpe=20,
    )


@pytest.fixture
def basic_fa_by_object_class_with_object_class_but_no_obligations(
    award_count_sub_schedule, award_count_submission, defc_codes
):
    basic_object_class = _major_object_class_with_children("001", [1])

    mommy.make(
        "financial_activities.FinancialAccountsByProgramActivityObjectClass",
        disaster_emergency_fund=DisasterEmergencyFundCode.objects.filter(code="M").first(),
        submission=SubmissionAttributes.objects.all().first(),
        object_class=basic_object_class[0],
        obligations_incurred_by_program_object_class_cpe=0,
        gross_outlay_amount_by_program_object_class_cpe=0,
    )


def _major_object_class_with_children(major_code, minor_codes):
    retval = []
    for minor_code in minor_codes:
        retval.append(
            mommy.make(
                "references.ObjectClass",
                id=minor_code,
                major_object_class=major_code,
                major_object_class_name=f"{major_code} name",
                object_class=f"000{minor_code}",
                object_class_name=f"000{minor_code} name",
            )
        )
    return retval