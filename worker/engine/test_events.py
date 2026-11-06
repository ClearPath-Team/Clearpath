"""Regression tests for Romanian speech, condensation and event selection."""
import copy
import unittest
from unittest.mock import patch

from worker.common import SAMPLES, read_json
from worker.engine.events import build_events


def node(index, role, name="", **fields):
    return {"id": f"n{index}", "order": index, "role": role, "name": name, **fields}


class EventsTests(unittest.TestCase):
    def test_samples_are_translated_instead_of_copied(self):
        source = read_json(SAMPLES / "nodes.json")
        original = copy.deepcopy(source)
        result = build_events(source)
        speech = {event["node_id"]: event["text"] for event in result["events"]}
        self.assertEqual(result["lang"], "ro")
        nodes = {n["selector"]: n for n in source["nodes"]}
        heading = next(n for n in source["nodes"] if n["role"] == "heading" and n["level"] == 1)
        self.assertEqual(speech[None], f"Pagina {source['title']}")
        self.assertEqual(speech[nodes["#cart"]["id"]], "buton")
        self.assertEqual(speech[nodes["#product-image"]["id"]], "imagine fără descriere")
        self.assertEqual(speech[nodes["#email"]["id"]], "casetă de editare, necompletat")
        self.assertEqual(speech[heading["id"]], "Finalizează comanda, titlu nivel 1")
        self.assertEqual(speech[nodes["#name"]["id"]],
                         f"{nodes['#name']['name']}, casetă de editare, necompletat, obligatoriu")
        self.assertEqual(source, original)

    def test_controls_and_optional_states(self):
        cases = [
            ("input", "Email", {"required": True}, None, "Email, casetă de editare, necompletat, obligatoriu"),
            ("textbox", "Cod", {}, "0", "Cod, casetă de editare, conține 0"),
            ("checkbox", "Accept", {"checked": True}, None, "Accept, casetă de bifare, bifat"),
            ("checkbox", "Accept", {"checked": False}, None, "Accept, casetă de bifare, nebifat"),
            ("checkbox", "Toate", {"checked": "mixed"}, None, "Toate, casetă de bifare, parțial bifat"),
            ("radio", "Card", {"checked": False}, None, "Card, buton radio, neselectat"),
            ("radio", "Card", {"checked": True}, None, "Card, buton radio, selectat"),
            ("combobox", "Țară", {"expanded": False}, "România", "Țară, casetă combinată, România, restrâns"),
            ("button", "Meniu", {"disabled": True, "expanded": True}, None, "Meniu, buton, indisponibil, extins"),
        ]
        for role, name, states, value, expected in cases:
            with self.subTest(role=role, states=states):
                events = build_events({"nodes": [node(0, role, name, states=states, value=value)]})["events"]
                self.assertEqual(events[1]["text"], expected)

    def test_landmarks_images_lists_and_unnamed_links(self):
        cases = {
            "banner": "reper antet", "navigation": "reper navigare",
            "main": "reper conținut principal", "contentinfo": "reper subsol",
            "search": "reper căutare", "form": "reper formular",
            "region": "regiune", "complementary": "reper complementar", "link": "link",
        }
        for role, expected in cases.items():
            with self.subTest(role=role):
                self.assertEqual(build_events({"nodes": [node(0, role)]})["events"][1]["text"], expected)
        source = {"nodes": [node(0, "image", "Pantofi"), node(1, "list", list_size=0)]}
        self.assertEqual([event["text"] for event in build_events(source)["events"]][1:],
                         ["Pantofi, imagine", "listă cu 0 elemente"])

    def test_text_merges_before_truncation_and_skips_third_parent(self):
        source = {"nodes": [
            node(0, "text", "unu doi trei patru cinci șase șapte", parent="p1"),
            node(1, "text", "opt nouă zece unsprezece doisprezece treisprezece", parent="p1"),
            node(2, "text", "Al doilea", parent="p2"),
            node(3, "text", "Omis", parent="p3"), node(4, "button", "Continuă"),
            node(5, "text", "Text nou", parent="p4"),
        ]}
        events = build_events(source)["events"]
        self.assertEqual([event["node_id"] for event in events], [None, "n0", "n2", "n4", "n5"])
        self.assertEqual(events[1]["text"], "unu doi trei patru cinci șase șapte opt nouă zece unsprezece doisprezece...")

    def test_cap_reserves_title_and_replaces_static_text_in_reading_order(self):
        source = {"nodes": [node(0, "text", "Static"), node(1, "button", "Primul"),
                            node(2, "text", "Static doi"), node(3, "button", "Al doilea"),
                            node(4, "button"), node(5, "textbox")]}
        with patch("worker.engine.events.MAX_EVENTS", 5):
            events = build_events(source)["events"]
        self.assertEqual([event["node_id"] for event in events], [None, "n1", "n3", "n4", "n5"])
        self.assertEqual([event["seq"] for event in events], list(range(5)))

    def test_protection_stops_after_first_eighty_nodes(self):
        source = {"nodes": [node(i, "button", f"B{i}") for i in range(80)] + [node(80, "button")]}
        source["nodes"][0] = node(0, "text", "Static")
        with patch("worker.engine.events.MAX_EVENTS", 3):
            events = build_events(source)["events"]
        self.assertEqual([event["node_id"] for event in events], [None, "n0", "n1"])

    def test_empty_input_and_unsorted_order(self):
        self.assertEqual(build_events({"nodes": []})["events"], [{"seq": 0, "node_id": None, "text": "Pagina"}])
        source = {"nodes": [node(2, "link", "Doi"), node(0, "button", "Zero")]}
        self.assertEqual([event["node_id"] for event in build_events(source)["events"]], [None, "n0", "n2"])


    def test_english_role_and_state_announcements(self):
        cases = [
            ("heading", "Welcome", {"level": 2}, "Welcome, heading level 2"),
            ("button", "Submit", {}, "Submit, button"),
            ("link", "", {}, "link"),
            ("textbox", "Search", {"states": {}}, "Search, edit, blank"),
            ("input", "Email", {"value": "a@example.org"}, "Email, edit, contains a@example.org"),
            ("checkbox", "Accept", {"states": {"checked": True}}, "Accept, check box, checked"),
            ("checkbox", "Accept", {"states": {"checked": False}}, "Accept, check box, not checked"),
            ("radio", "Payment", {"states": {"checked": False}}, "Payment, radio button, not selected"),
            ("combobox", "Country", {}, "Country, combo box"),
            ("image", "", {}, "graphic unlabelled"),
            ("banner", "", {}, "banner landmark"),
            ("navigation", "Main navigation", {}, "Main navigation, navigation landmark"),
            ("button", "Menu", {"states": {"required": True, "disabled": True}}, "Menu, button, required, unavailable"),
        ]
        for role, name, props, expected in cases:
            with self.subTest(role=role, name=name):
                speech = build_events({"nodes": [node(0, role, name, **props)]}, lang="en")
                self.assertEqual(speech["lang"], "en")
                self.assertEqual(speech["events"][1]["text"], expected)

    def test_english_title_and_invalid_lang(self):
        self.assertEqual(build_events({"title": "Example", "nodes": []}, lang="en")["events"][0]["text"],
                         "Page Example")
        with self.assertRaises(ValueError):
            build_events({"nodes": []}, lang="fr")


if __name__ == "__main__":
    unittest.main()
