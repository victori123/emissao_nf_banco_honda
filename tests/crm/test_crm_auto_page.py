from src.crm.pages.crm_auto_page import CrmAutoPage


def test_extract_tag_values_from_observation():
    page = object.__new__(CrmAutoPage)
    observacoes = [
        {
            "Observação": (
                "Texto inicial\n"
                "[CFOP]5405[/CFOP]\n"
                "[RENAVAN]123456[/RENAVAN]\n"
                "[OBSERVAÇÃO]observação de teste[/OBSERVAÇÃO]\n"
                "[ALIENAÇÃO]ali 123[/ALIENAÇÃO]\n"
                "[PROPOSTA]proposta 999[/PROPOSTA]"
            )
        },
        {"Observação": "[SEMINOVO]sim[/SEMINOVO]"},
    ]

    assert page.extract_cfop_from_observacao(observacoes) == "5405"
    assert page.extract_renavan_from_observacao(observacoes) == "123456"
    assert page.extract_obs_nbs_from_observacao(observacoes) == "observação de teste"
    assert page.extract_alienacao_nbs_from_observacao(observacoes) == "ali 123"
    assert page.extract_proposta_nbs_from_observacao(observacoes) == "proposta 999"
    assert page.check_semi_novo_from_observacao(observacoes) is True
