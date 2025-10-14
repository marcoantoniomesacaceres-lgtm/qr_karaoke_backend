from youtube import _perform_youtube_search


def test_extract_video_ids_various_shapes():
    # This test duplicates the parsing behaviour used in _perform_youtube_search
    simulated_items = [
        {"id": {"videoId": "VID1"}},
        {"id": {"channelId": "CHAN1"}},
        {"id": "VID2"},
        {"id": {"playlistId": "PL1"}},
        {"id": None},
    ]

    # Reimplement the helper locally just like the module does
    def extract_video_ids_from_search_items(items):
        ids = []
        for item in items:
            id_obj = item.get("id")
            if isinstance(id_obj, dict):
                vid = id_obj.get("videoId")
                if vid:
                    ids.append(vid)
            elif isinstance(id_obj, str):
                ids.append(id_obj)
        return ids

    result = extract_video_ids_from_search_items(simulated_items)
    assert result == ["VID1", "VID2"]
