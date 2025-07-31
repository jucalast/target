"""Tests for the SIDRA Mapper service."""
import pytest
from etl_pipeline.app.services.sidra_mapper import SIDRAMapper, SIDRAParameter


def test_sidra_parameter_get_matching_codes():
    """Test the SIDRAParameter get_matching_codes method."""
    param = SIDRAParameter(
        code='200',
        name='Faixa etária',
        description='Faixas de idade da população',
        values={
            '1933': '14 a 17 anos',
            '1934': '18 a 24 anos',
            '1935': '25 a 39 anos',
            '1936': '40 a 59 anos',
            '1937': '60 anos ou mais'
        }
    )

    # Test exact matches
    assert set(param.get_matching_codes(['14 a 17 anos'])) == {'1933'}
    assert set(param.get_matching_codes(['18 a 24'])) == {'1934'}

    # Test partial matches
    assert set(param.get_matching_codes(['anos'])) == {'1933', '1934', '1935', '1936', '1937'}
    assert set(param.get_matching_codes(['60'])) == {'1937'}

    # Test no matches
    assert param.get_matching_codes(['criança']) == []
    assert param.get_matching_codes(['']) == []


class TestSIDRAMapper:
    """Test suite for the SIDRAMapper class."""

    @pytest.fixture


    def mapper(self):
        """Create a SIDRAMapper instance for testing."""
        return SIDRAMapper()


    def test_initialization(self, mapper):
        """Test that the mapper initializes with the correct parameters."""
        assert '200' in mapper.parameters  # Age
        assert '143' in mapper.parameters  # Gender
        assert '276' in mapper.parameters  # Education
        assert '6793' in mapper.parameters  # Income
        assert '11046' in mapper.parameters  # Expense categories

        # Check some term mappings
        assert mapper.term_to_parameter['idade'] == '200'
        assert mapper.term_to_parameter['renda'] == '6793'
        assert mapper.term_to_parameter['escolaridade'] == '276'


    def test_map_terms_to_sidra_parameters_direct_matches(self, mapper):
        """Test mapping with direct term matches."""
        # Test with direct term matches
        result = mapper.map_terms_to_sidra_parameters(['idade', 'renda'])

        # Should map to age (200) and income (6793) parameters
        assert '200' in result['classificacoes']
        assert '6793' in result['variaveis']

        # Check matched terms
        assert 'idade' in ' '.join(term.lower() for term in result['matched_terms']['200']['matched_terms'])
        assert 'renda' in ' '.join(term.lower() for term in result['matched_terms']['6793']['matched_terms'])


    def test_map_terms_to_sidra_parameters_fuzzy_matches(self, mapper):
        """Test mapping with fuzzy matches to parameter names/descriptions."""
        # These terms don't have direct mappings but should match parameter names/descriptions
        result = mapper.map_terms_to_sidra_parameters(['salário', 'gênero', 'estudo'])

        # Should map to income (6793), gender (143), and education (276) parameters
        assert '6793' in result['variaveis']  # Income
        assert '143' in result['classificacoes']  # Gender
        assert '276' in result['classificacoes']  # Education


    def test_map_terms_with_preferred_table(self, mapper):
        """Test mapping with a preferred table that limits available parameters."""
        # POF table (7482) has different parameters than PNAD (6401)
        result = mapper.map_terms_to_sidra_parameters(
            terms=['idade', 'renda', 'consumo'],
            preferred_table='7482'  # POF - Despesas
        )

        # Should only include parameters available in the POF table
        assert result['tabela'] == '7482'
        assert '11046' in result['classificacoes']  # Despesas

        # Age (200) and income (6793) parameters are not in the POF table,
        # so they should not be included
        assert '200' not in result['classificacoes']
        assert '6793' not in result['variaveis']


    def test_refine_parameter_values(self, mapper):
        """Test refining parameter values based on input terms."""
        # Start with a basic result
        result = {
            'tabela': '6401',
            'variaveis': [],
            'classificacoes': {
                '200': 'all',  # Age
                '143': 'all'   # Gender
            },
            'localidades': ['BR'],
            'periodo': 'last',
            'matched_terms': {}
        }

        # Refine with terms that match specific values
        mapper._refine_parameter_values(result, ['mulher', '25 a 39 anos'])

        # Should have specific values for gender and age
        assert result['classificacoes']['143'] == 'F'  # Female
        assert result['classificacoes']['200'] == '1935'  # 25-39 years


    def test_suggest_tables(self, mapper):
        """Test suggesting relevant tables based on input terms."""
        # Test with terms related to income and work
        suggestions = mapper.suggest_tables(['renda', 'trabalho', 'desemprego'])

        # Should suggest PNAD Contínua (6401) first
        assert len(suggestions) > 0
        assert suggestions[0]['table_code'] == '6401'

        # Test with terms related to expenses
        suggestions = mapper.suggest_tables(['despesa', 'alimentação', 'transporte'])
        assert any(s['table_code'] == '7482' for s in suggestions)  # POF - Despesas


    def test_get_table_info(self, mapper):
        """Test getting information about a SIDRA table."""
        # Test with existing table
        table_info = mapper.get_table_info('6401')
        assert table_info['name'] == 'PNAD Contínua - Rendimento e outras características'
        assert 'parameters' in table_info

        # Test with non-existent table
        assert mapper.get_table_info('9999') == {}


    def test_get_parameter_info(self, mapper):
        """Test getting information about a SIDRA parameter."""
        # Test with existing parameter
        param_info = mapper.get_parameter_info('200')
        assert param_info['name'] == 'Faixa etária'
        assert 'values' in param_info

        # Test with non-existent parameter
        assert mapper.get_parameter_info('9999') == {}


    def test_map_terms_with_no_matches(self, mapper):
        """Test mapping with terms that have no direct or fuzzy matches."""
        result = mapper.map_terms_to_sidra_parameters(['xyz123', 'abc456'])

        # Should use default parameters
        assert '200' in result['classificacoes']  # Age
        assert '6793' in result['variaveis']  # Income
        assert '11046' in result['classificacoes']  # Expenses


    def test_map_terms_with_specific_values(self, mapper):
        """Test mapping with terms that match specific parameter values."""
        result = mapper.map_terms_to_sidra_parameters(
            ['mulher', '25 a 39 anos', 'superior completo']
        )

        # Should have specific values for gender, age, and education
        assert result['classificacoes']['143'] == 'F'  # Female
        assert result['classificacoes']['200'] == '1935'  # 25-39 years
        assert '29579' in result['classificacoes']['276']  # Superior completo


    def test_map_terms_with_multiple_matches(self, mapper):
        """Test mapping with terms that match multiple parameter values."""
        result = mapper.map_terms_to_sidra_parameters(
            ['mulher', 'homem', '14 a 17 anos', '18 a 24 anos']
        )

        # Should include both genders and both age ranges
        assert 'M' in result['classificacoes']['143']
        assert 'F' in result['classificacoes']['143']
        assert '1933' in result['classificacoes']['200']  # 14-17
        assert '1934' in result['classificacoes']['200']  # 18-24
