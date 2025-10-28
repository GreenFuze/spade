export interface User {
	id: number;
	username: string;
	email: string;
	createdAt: Date;
	active: boolean;
}

export class UserService {
	private users: Map<number, User> = new Map();
	private nextId = 1;

	createUser(username: string, email: string): User {
		const user: User = {
			id: this.nextId++,
			username,
			email,
			createdAt: new Date(),
			active: true,
		};
		this.users.set(user.id, user);
		return user;
	}

	getUser(id: number): User | undefined {
		return this.users.get(id);
	}

	getUserByUsername(username: string): User | undefined {
		for (const user of this.users.values()) {
			if (user.username === username) {
				return user;
			}
		}
		return undefined;
	}

	getAllUsers(): User[] {
		return Array.from(this.users.values());
	}

	updateUser(user: User): boolean {
		if (this.users.has(user.id)) {
			this.users.set(user.id, user);
			return true;
		}
		return false;
	}

	deleteUser(id: number): boolean {
		return this.users.delete(id);
	}
}
