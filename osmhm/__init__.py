import fetch
import filters
import inserts
import tables
import config
import send_notification


def run(time_type='hour', history=True, suspicious=False, monitor=True,
        notification=False):
    """
    """
    import osmhm
    import osmdt
    import datetime
    import time

    while True:

        sequence = osmhm.fetch.fetch_last_read()

        if not sequence:
            osmhm.fetch.fetch_next(time_type=time_type, reset=True)
            sequence = osmhm.fetch.fetch_last_read()

        if sequence['read_flag'] is False:
            print "Processing sequence %s." % (sequence['sequencenumber'])

            data_stream = osmdt.fetch(sequence['sequencenumber'], time=time_type)
            data_object = osmdt.process(data_stream)

            changesets = osmdt.extract_changesets(data_object)
            objects = osmdt.extract_objects(data_object)
            users = osmdt.extract_users(data_object)

            if history:
                osmhm.inserts.insert_all_changesets(changesets)

            if suspicious:
                osmhm.filters.suspiciousFilter(changesets)

            if monitor:
                osmhm.filters.objectFilter(objects, notification=notification)
                osmhm.filters.userFilter(changesets, notification=notification)
                osmhm.filters.user_object_filter(objects, notification=notification)
                osmhm.filters.keyFilter(objects, notification=notification)

            osmhm.inserts.insert_file_read()
            print "Finished processing %s." % (sequence['sequencenumber'])

        if sequence['timetype'] == 'minute':
            delta_time = 1
            extra_time = 10
        elif sequence['timetype'] == 'hour':
            delta_time = 60
            extra_time = 62
        elif sequence['timetype'] == 'day':
            delta_time = 1440
            extra_time = 300

        next_time = datetime.datetime.strptime(sequence['timestamp'],
                      "%Y-%m-%dT%H:%M:%SZ") + datetime.timedelta(minutes=delta_time)

        if datetime.datetime.utcnow() < next_time:
            sleep_time = (next_time - datetime.datetime.utcnow()).seconds + delta_time
            print "Waiting %2.1f seconds for the next file." % (sleep_time)
        else:
            sleep_time = 0

        time.sleep(sleep_time)

        count = 0
        while True:
            try:
                count += 1
                osmhm.fetch.fetch_next(sequence['sequencenumber'], time_type=time_type)
                break
            except:
                if count == 5:
                    msg = 'New state file not retrievable after five times.'
                    raise Exception(msg)
                print "Waiting %2.1f more seconds..." % (extra_time)
                time.sleep(extra_time)
