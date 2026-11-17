import unittest

from streamlit.testing.v1 import AppTest

from quest_data import UNIT_CATALOG


def _complete_current_scenario(at: AppTest) -> str:
    unit_name = at.session_state["hq_selected_unit"]
    scenario_id = at.session_state["hq_selected_scenario_id"]
    scenario = next(
        item
        for item in UNIT_CATALOG[unit_name]["scenarios"]
        if item["scenario_id"] == scenario_id
    )
    at.session_state["hq_submissions"] = {
        mission["id"]: {
            "selected_idx": mission.get("answer_index", 0),
            "is_correct": True,
            "rationale": "학생이 작성한 임상 판단 근거입니다.",
            "rationale_status": "개인 서술 완료",
            "ai_individual_feedback": "피드백 확인 완료",
        }
        for mission in scenario["missions"]
    }
    return unit_name


def _button_count(at: AppTest, key: str) -> int:
    return sum(1 for button in at.button if button.key == key)


class IntegratedAppTest(unittest.TestCase):
    def test_simulation_lab_unlocks_only_after_all_missions(self):
        at = AppTest.from_file("app_integrated.py", default_timeout=30).run()
        self.assertFalse(at.exception)
        self.assertEqual(_button_count(at, "integrated_simulation_start"), 0)

        _complete_current_scenario(at)
        at.run(timeout=30)

        self.assertFalse(at.exception)
        self.assertEqual(_button_count(at, "integrated_simulation_start"), 1)

    def test_launch_hands_unit_to_rag_page_and_clears_stale_unit_state(self):
        at = AppTest.from_file("app_integrated.py", default_timeout=30).run()
        unit_name = _complete_current_scenario(at)
        at.session_state["ragpbl_last_unit"] = "이전 단원"
        at.session_state["ragpbl_discovery"] = "stale result"
        at.run(timeout=30)

        at.button(key="integrated_simulation_start").click().run(timeout=30)

        self.assertFalse(at.exception)
        self.assertEqual(at.session_state["ragpbl_unit"], unit_name)
        self.assertEqual(at.session_state["ragpbl_last_unit"], unit_name)
        self.assertEqual(at.session_state["ragpbl_entry_source"], "mission_room")
        self.assertIsNone(at.session_state["ragpbl_discovery"])


if __name__ == "__main__":
    unittest.main()
