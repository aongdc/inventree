import envs

def users(as_dict=True):
    users = dict() if as_dict else []

    with open(envs.USERS_TXT, 'r') as f:
        all_users = f.readlines()
        if as_dict:
            for i, user in enumerate(all_users):
                users[user.strip('\n')] = i + 1
        else:
            for user in all_users:
                users.append(user.strip('\n'))
    f.close()

    return users

if __name__ == '__main__':
    print(users(as_dict=False))
    print(users())
