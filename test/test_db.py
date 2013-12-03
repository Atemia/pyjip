#!/usr/bin/env python
import os
import jip
import jip.db
import datetime


def test_command_change_save(tmpdir):
    db_file = os.path.join(str(tmpdir), "test.db")
    jip.db.init(db_file)
    j = jip.db.Job()
    j.command = "A"
    # save the job
    jip.db.save(j)
    assert jip.db.get(j.id).command == "A"
    j.command = "B"
    jip.db.save(j)
    assert jip.db.get(j.id).command == "B"


def test_updating_state(tmpdir):
    db_file = os.path.join(str(tmpdir), "test.db")
    jip.db.init(db_file)
    j = jip.db.Job()

    # save the job
    jip.db.save(j)

    # get a fresh copy from the database and ensure initial states
    j = jip.db.get(j.id)
    assert j is not None
    assert j.create_date is not None
    assert j.start_date is None
    assert j.finish_date is None
    assert j.job_id is None
    assert j.state == jip.db.STATE_HOLD
    assert len(j.pipe_to) == 0
    assert len(j.pipe_from) == 0

    # set new values
    date = datetime.datetime.now()
    j.job_id = 10
    j.start_date = date
    j.finish_date = date
    j.state = jip.db.STATE_DONE

    # update
    jip.db.update_job_states(j)
    fresh = jip.db.get(j.id)

    assert fresh is not None
    assert fresh.create_date is not None
    assert fresh.start_date == date
    assert fresh.finish_date == date
    assert fresh.job_id == "10"
    assert fresh.state == jip.db.STATE_DONE


def test_update_archived_single(tmpdir):
    db_file = os.path.join(str(tmpdir), "test.db")
    jip.db.init(db_file)
    j = jip.db.Job()
    jip.db.save(j)
    assert not jip.db.get(j.id).archived
    jip.db.update_archived(j, True)
    assert jip.db.get(j.id).archived


def test_update_archived_multiple(tmpdir):
    db_file = os.path.join(str(tmpdir), "test.db")
    jip.db.init(db_file)
    j1 = jip.db.Job()
    j2 = jip.db.Job()
    jip.db.save([j1, j2])
    assert not jip.db.get(j1.id).archived
    assert not jip.db.get(j2.id).archived
    jip.db.update_archived([j1, j2], True)
    assert jip.db.get(j1.id).archived
    assert jip.db.get(j2.id).archived


def test_update_state_of_non_existing_job(tmpdir):
    db_file = os.path.join(str(tmpdir), "test.db")
    jip.db.init(db_file)
    j = jip.db.Job()
    j.id = 100
    jip.db.update_job_states(j)
    assert len(jip.db.get_all()) == 0


def test_delete_single_job(tmpdir):
    db_file = os.path.join(str(tmpdir), "test.db")
    jip.db.init(db_file)
    j = jip.db.Job()
    jip.db.save(j)
    assert len(jip.db.get_all()) == 1
    jip.db.delete(j)
    assert len(jip.db.get_all()) == 0


def test_get_state(tmpdir):
    db_file = os.path.join(str(tmpdir), "test.db")
    jip.db.init(db_file)
    j = jip.db.Job()
    jip.db.save(j)
    assert jip.db.get_current_state(j) == jip.db.STATE_HOLD
    j.state = jip.db.STATE_DONE
    jip.db.update_job_states(j)
    assert jip.db.get_current_state(j) == jip.db.STATE_DONE


def test_delete_job_with_parent_job(tmpdir):
    db_file = os.path.join(str(tmpdir), "test.db")
    jip.db.init(db_file)
    parent = jip.db.Job()
    child = jip.db.Job()
    child.dependencies.append(parent)
    jip.db.save([parent, child])
    assert len(jip.db.get_all()) == 2
    jip.db.delete(child)
    assert len(jip.db.get_all()) == 1
    child = jip.db.get(child.id)
    assert child is None
    parent = jip.db.get(parent.id)
    assert parent is not None
    assert len(parent.children) == 0

    # check the raw table
    s = jip.db.job_dependencies.select()
    c = jip.db.engine.connect()
    res = c.execute(s)
    count = sum(map(lambda x: 1, res))
    c.close()
    assert count == 0


def test_delete_unknown_job(tmpdir):
    db_file = os.path.join(str(tmpdir), "test.db")
    jip.db.init(db_file)
    job = jip.db.Job()
    job.id = 100
    assert len(jip.db.get_all()) == 0
    jip.db.delete(job)
    assert len(jip.db.get_all()) == 0


def test_cascaded_save(tmpdir):
    db_file = os.path.join(str(tmpdir), "test.db")
    jip.db.init(db_file)
    parent = jip.db.Job()
    child = jip.db.Job()
    child.dependencies.append(parent)
    jip.db.save([parent])
    assert len(jip.db.get_all()) == 2