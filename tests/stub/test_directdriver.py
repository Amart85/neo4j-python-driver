#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Copyright (c) 2002-2020 "Neo4j,"
# Neo4j Sweden AB [http://neo4j.com]
#
# This file is part of Neo4j.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import pytest

from neo4j.exceptions import ServiceUnavailable
from neo4j._exceptions import BoltHandshakeError

from neo4j import (
    GraphDatabase,
    BoltDriver,
    Query,
    WRITE_ACCESS,
)

from tests.stub.conftest import (
    StubCluster,
)

# python -m pytest tests/stub/test_directdriver.py


driver_config = {
    "secure": False,
    # "trust": None, # TODO: Investigate why this seem to hang the max_retry_time
    "user_agent": "test",
    "max_age": 1000,
    "max_size": 10,
    # "connection_acquisition_timeout": 1, # TODO: Investigate why this seem to hang the max_retry_time
    # "connection_timeout": 1, # TODO: Investigate why this seem to hang the max_retry_time
    "keep_alive": False,
    "max_retry_time": 1,
    "resolver": None,
}

session_config = {
    # "fetch_size": 100,
    # "database": "default",
    # "bookmarks": ["bookmark-1", ],
    "default_access_mode": WRITE_ACCESS,
    "acquire_timeout": 1.0,
    "max_retry_time": 1.0,
    "initial_retry_delay": 1.0,
    "retry_delay_multiplier": 1.0,
    "retry_delay_jitter_factor": 0.1,
}


@pytest.mark.parametrize(
    "test_script",
    [
        "v3/empty.script",
        "v4x0/empty.script",
    ]
)
def test_bolt_uri_constructs_bolt_driver(driver_info, test_script):
    # python -m pytest tests/stub/test_directdriver.py -s -v -k test_bolt_uri_constructs_bolt_driver
    with StubCluster(test_script):
        uri = "bolt://127.0.0.1:9001"
        with GraphDatabase.driver(uri, auth=driver_info["auth_token"]) as driver:
            assert isinstance(driver, BoltDriver)


@pytest.mark.parametrize(
    "test_script, test_expected",
    [
        ("v1/empty_explicit_hello_goodbye.script", ServiceUnavailable),
        ("v2/empty_explicit_hello_goodbye.script", ServiceUnavailable),
        ("v3/empty_explicit_hello_goodbye.script", None),
        ("v4x0/empty_explicit_hello_goodbye.script", None),
    ]
)
def test_direct_driver_handshake_negotiation(driver_info, test_script, test_expected):
    # python -m pytest tests/stub/test_directdriver.py -s -v -k test_direct_driver_handshake_negotiation
    with StubCluster(test_script):
        uri = "bolt://127.0.0.1:9001"
        if test_expected:
            with pytest.raises(test_expected) as error:
                driver = GraphDatabase.driver(uri, auth=driver_info["auth_token"], **driver_config)
            assert isinstance(error.value.__cause__, BoltHandshakeError)
        else:
            driver = GraphDatabase.driver(uri, auth=driver_info["auth_token"], **driver_config)
            assert isinstance(driver, BoltDriver)
            driver.close()


def test_direct_driver_with_wrong_port(driver_info):
    # python -m pytest tests/stub/test_directdriver.py -s -v -k test_direct_driver_with_wrong_port
    uri = "bolt://127.0.0.1:9002"
    with pytest.raises(ServiceUnavailable):
        driver = GraphDatabase.driver(uri, auth=driver_info["auth_token"], **driver_config)
        # assert isinstance(driver, BoltDriver)
        # with pytest.raises(ServiceUnavailable):
        #     driver.verify_connectivity()


@pytest.mark.parametrize(
    "test_script, test_expected",
    [
        ("v3/return_1_port_9001.script", "Neo4j/3.0.0"),
        ("v4x0/return_1_port_9001.script", "Neo4j/4.0.0"),
    ]
)
def test_direct_verify_connectivity(driver_info, test_script, test_expected):
    # python -m pytest tests/stub/test_directdriver.py -s -v -k test_direct_verify_connectivity
    with StubCluster(test_script):
        uri = "bolt://127.0.0.1:9001"
        with GraphDatabase.driver(uri, auth=driver_info["auth_token"], **driver_config) as driver:
            assert isinstance(driver, BoltDriver)
            assert driver.verify_connectivity() == test_expected


@pytest.mark.parametrize(
    "test_script",
    [
        "v3/disconnect_on_run.script",
        "v4x0/disconnect_on_run.script",
    ]
)
def test_direct_verify_connectivity_disconnect_on_run(driver_info, test_script):
    # python -m pytest tests/stub/test_directdriver.py -s -v -k test_direct_verify_connectivity_disconnect_on_run
    with StubCluster(test_script):
        uri = "bolt://127.0.0.1:9001"
        with GraphDatabase.driver(uri, auth=driver_info["auth_token"], **driver_config) as driver:
            with pytest.raises(ServiceUnavailable):
                driver.verify_connectivity()


@pytest.mark.parametrize(
    "test_script",
    [
        "v3/disconnect_on_run.script",
        "v4x0/disconnect_on_run.script",
    ]
)
def test_direct_disconnect_on_run(driver_info, test_script):
    # python -m pytest tests/stub/test_directdriver.py -s -v -k test_direct_disconnect_on_run
    with StubCluster(test_script):
        uri = "bolt://127.0.0.1:9001"
        with GraphDatabase.driver(uri, auth=driver_info["auth_token"], **driver_config) as driver:
            with pytest.raises(ServiceUnavailable):
                with driver.session(**session_config) as session:
                    session.run("RETURN 1 AS x").consume()


@pytest.mark.parametrize(
    "test_script",
    [
        "v3/disconnect_on_pull_all.script",
        "v4x0/disconnect_on_pull.script",
    ]
)
def test_direct_disconnect_on_pull_all(driver_info, test_script):
    # python -m pytest tests/stub/test_directdriver.py -s -v -k test_direct_disconnect_on_pull_all
    with StubCluster(test_script):
        uri = "bolt://127.0.0.1:9001"
        with GraphDatabase.driver(uri, auth=driver_info["auth_token"], **driver_config) as driver:
            with pytest.raises(ServiceUnavailable):
                with driver.session(**session_config) as session:
                    session.run("RETURN $x", {"x": 1}).consume()


@pytest.mark.parametrize(
    "test_script",
    [
        "v3/disconnect_after_init.script",
        "v4x0/disconnect_after_init.script",
    ]
)
def test_direct_session_close_after_server_close(driver_info, test_script):
    # python -m pytest tests/stub/test_directdriver.py -s -v -k test_direct_session_close_after_server_close
    with StubCluster(test_script):
        uri = "bolt://127.0.0.1:9001"

        with GraphDatabase.driver(uri, auth=driver_info["auth_token"], **driver_config) as driver:
            with driver.session(**session_config) as session:
                with pytest.raises(ServiceUnavailable):
                    session.write_transaction(lambda tx: tx.run(Query("CREATE (a:Item)", timeout=1)))
