Feature: Slingshot should yield valid results for the function under test access

    Background:
        Given The function under test has the signature access-fname-int_amode

    Scenario: Running testcase 1084 of access
        Given the specified testcase is 1084
        When running the testcase
        Then slingshot is detecting a PASS

