import unittest

from csv_loader import load_disease_medication_references
from medication_safety import has_medical_review


class MedicationSafetyTests(unittest.TestCase):
    def test_loads_unverified_reference_list_for_model_disease_labels(self):
        references = load_disease_medication_references()

        self.assertIn("malaria", references)
        self.assertIn("dimorphic hemmorhoids(piles)", references)
        self.assertIn("common_medications", references["malaria"])
        self.assertNotIn("review_status", references["malaria"])

    def test_unreviewed_seed_record_is_not_approved(self):
        record = {
            "recommended_medicine": "Sample medicine",
            "adult_dosage": "Sample dosage",
        }
        self.assertFalse(has_medical_review(record))

    def test_requires_review_status_and_provenance(self):
        record = {
            "review_status": "approved",
            "reviewed_by": "Clinical reviewer",
            "reviewed_at": "2026-01-01",
            "source": "https://example.org/clinical-guidance",
        }
        self.assertTrue(has_medical_review(record))
        record["source"] = " "
        self.assertFalse(has_medical_review(record))
        record["source"] = "https://example.org/clinical-guidance"
        record["reviewed_at"] = "not-a-date"
        self.assertFalse(has_medical_review(record))


if __name__ == "__main__":
    unittest.main()
