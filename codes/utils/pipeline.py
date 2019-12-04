import cStringIO
import csv
import json
import operator


class Pipeline(object):

    # return unique keys from list
    def getcsvheaders(self, data=None):

        # if not data:
        #     raise ImportExportError("Provide data to retrive headers")

        # HACK to keep these fields at top in csv
        header = {'url': 33300, 'Error': 32000}
        for dict_ in data:
            # try:
            for key in dict_.keys():
                if key not in header.keys():
                    header[key] = 1
                else:
                    header[key] += 1
            # except:
            #     pass

        result = []

        header = sorted(
            header.items(), key=operator.itemgetter(1), reverse=True
        )
        for key in header:
            result.append(key[0])
        return result

    def convertjson(self, data_list):
        csv_output = cStringIO.StringIO()

        # url = obj.request.URL
        # id_ = urlparse(url).path.split('/')[1]

        csv_headers = self.getcsvheaders(data_list)
        # if not csv_headers:
        #     raise BadRequest("check json data, no keys found")

        try:
            '''The optional restval parameter specifies the value to be written
            if the dictionary is missing a key in fieldnames. If the
            dictionary passed to the writerow() method contains a key not
            found in fieldnames, the optional extrasaction parameter indicates
            what action to take. If it is set to 'raise' a ValueError is
            raised. If it is set to 'ignore', extra values in the dictionary
            are ignored.'''
            writer = csv.DictWriter(
                csv_output,
                fieldnames=csv_headers,
                restval='Field NA',
                extrasaction='raise',
                dialect='excel'
            )
            writer.writeheader()
            for data in data_list:
                for key in data.keys():
                    # if not data[key]:
                    #     data[key] = "Null"

                    # converting list and dict to quoted json
                    data[key] = json.dumps(data[key])

                writer.writerow(data)
        except IOError as (errno, strerror):
            print("I/O error({0}): {1}".format(errno, strerror))

        data = csv_output.getvalue()
        csv_output.close()
        return data

    def converttojson(self, data=None):
        # if not data:
        #     raise ImportExportError("Provide data to jsonify")

        reader = csv.DictReader(data)
        data = []
        for row in reader:
            data.append(row)
        # jsonify quoted json values
        data = self.jsonify(data)
        self.filter_keys(data=data)
        # temp func to get good json data
        for index in range(len(data)):
            for k, v in data[index].items():
                if v == "Null":
                    data[index][k] = 0

        return data

    # jsonify quoted json values
    def jsonify(self, data):
        if isinstance(data, dict):
            for key in data.keys():
                data[key] = self.jsonify(data[key])
        elif isinstance(data, list):
            for index in range(len(data)):
                data[index] = self.jsonify(data[index])
        try:
            data = json.loads(data)
        # TODO raise the error into log_file
        except:
            pass
        finally:
            return data

    def filter_keys(self, data=None, excluded=None):
        if isinstance(data, list):
            for index in range(len(data)):
                self.filter_keys(data[index], excluded)
        elif isinstance(data, dict):
            for key in data.keys():
                # or key in excluded:
                if data[key] == "Field NA":
                    del data[key]

        return True
