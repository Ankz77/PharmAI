import unittest

from symptom_matching import explain_symptom_matches, normalize_symptom


class SymptomMatchingTests(unittest.TestCase):
    def test_normalizes_spaces_around_underscores(self):
        self.assertEqual(normalize_symptom("dischromic _patches"), "dischromic_patches")
        self.assertEqual(normalize_symptom("sunken eyes"), "sunken_eyes")

    def test_reports_symptoms_in_best_matching_disease_pattern(self):
        patterns = [
            {"vomiting", "diarrhoea", "sunken_eyes", "dehydration"},
            {"headache", "high_fever"},
        ]

        result = explain_symptom_matches(
            ["vomiting", "diarrhoea", "sunken_eyes"],
            patterns,
        )

        self.assertEqual(result, ["diarrhoea", "sunken_eyes", "vomiting"])

    def test_returns_empty_when_no_selected_symptoms_match(self):
        self.assertEqual(
            explain_symptom_matches(["unknown_symptom"], [{"vomiting"}]),
            [],
        )


if __name__ == "__main__":
    unittest.main()
