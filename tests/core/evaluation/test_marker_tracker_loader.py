from rasa.shared.core.events import UserUttered
from rasa.shared.core.trackers import DialogueStateTracker
from rasa.shared.core.domain import Domain
from rasa.shared.exceptions import RasaException
from rasa.core.evaluation.marker_tracker_loader import MarkerTrackerLoader
from rasa.core.tracker_store import InMemoryTrackerStore, TrackerStore
import pytest


@pytest.fixture
def marker_trackerstore() -> TrackerStore:
    """Sets up a TrackerStore with 5 trackers in it."""
    domain = Domain.empty()
    store = InMemoryTrackerStore(domain)
    for i in range(5):
        tracker = DialogueStateTracker(str(i), None)
        tracker.update_with_events([UserUttered(str(j)) for j in range(10)], domain)
        store.save(tracker)

    return store


def test_load_sample(marker_trackerstore: TrackerStore):
    """Tests loading trackers using 'sample' strategy."""
    loader = MarkerTrackerLoader(marker_trackerstore, "sample", 3)
    result = list(loader.load())

    assert len(result) == 3

    senders = set()
    for item in result:
        assert marker_trackerstore.exists(item.sender_id)
        assert item.sender_id not in senders
        senders.add(item.sender_id)


def test_load_sample_with_seed(marker_trackerstore: TrackerStore):
    """Tests loading trackers using 'sample' strategy with seed set."""
    loader = MarkerTrackerLoader(marker_trackerstore, "sample", 3, seed=3)
    result = list(loader.load())
    expected_ids = ["1", "4", "3"]

    assert len(result) == 3

    for item, expected in zip(result, expected_ids):
        assert item.sender_id == expected
        assert marker_trackerstore.exists(item.sender_id)


def test_load_first_n(marker_trackerstore: TrackerStore):
    """Tests loading trackers using 'first_n' strategy."""
    loader = MarkerTrackerLoader(marker_trackerstore, "first_n", 3)
    result = list(loader.load())

    assert len(result) == 3

    for item in result:
        assert marker_trackerstore.exists(item.sender_id)


def test_load_all(marker_trackerstore: TrackerStore):
    """Tests loading trackers using 'all' strategy."""
    loader = MarkerTrackerLoader(marker_trackerstore, "all")
    result = list(loader.load())

    assert len(result) == len(list(marker_trackerstore.keys()))

    for item in result:
        assert marker_trackerstore.exists(item.sender_id)


def test_exception_invalid_strategy(marker_trackerstore: TrackerStore):
    """Tests an exception is thrown when an invalid strategy is used."""
    with pytest.raises(RasaException):
        MarkerTrackerLoader(marker_trackerstore, "summon")


def test_exception_no_count(marker_trackerstore: TrackerStore):
    """Tests an exception is thrown when no count is given for non-'all' strategies."""
    with pytest.raises(RasaException):
        MarkerTrackerLoader(marker_trackerstore, "sample")


def test_exception_zero_count(marker_trackerstore: TrackerStore):
    """Tests an exception is thrown when an invalid count is given."""
    with pytest.raises(RasaException):
        MarkerTrackerLoader(marker_trackerstore, "sample", 0)


def test_exception_negative_count(marker_trackerstore: TrackerStore):
    """Tests an exception is thrown when an invalid count is given."""
    with pytest.raises(RasaException):
        MarkerTrackerLoader(marker_trackerstore, "sample", -1)


def test_warn_seed_unnecessary(marker_trackerstore: TrackerStore):
    """Tests a warning is thrown when 'seed' is set for non-'sample' strategies."""
    with pytest.warns(UserWarning):
        MarkerTrackerLoader(marker_trackerstore, "first_n", 3, seed=5)


def test_warn_count_all_unnecessary(marker_trackerstore: TrackerStore):
    """Tests a warning is thrown when 'count' is set for strategy 'all'."""
    with pytest.warns(UserWarning):
        MarkerTrackerLoader(marker_trackerstore, "all", 3)


def test_warn_count_exceeds_store(marker_trackerstore: TrackerStore):
    """Tests a warning is thrown when 'count' is larger than the number of trackers."""
    loader = MarkerTrackerLoader(marker_trackerstore, "sample", 6)
    with pytest.warns(UserWarning):
        # Need to force the generator to evaluate to produce the warning
        list(loader.load())
